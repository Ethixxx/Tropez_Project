from Backend.API_Connector import requestors
from Backend.API_Key_Container.AccountDB import APIKeyManager
from Backend.FileDatabase.database import fileDatabase
from Backend.API_Connector.AISummarizerService import AISummarizerService

from urllib import parse
import enum

import heapq

import threading

import pathlib

class FileOrchestrator:
    def __init__(self, api_key_manager: APIKeyManager, file_database: fileDatabase):
        """
        Initializes the FileOrchestrator with an API key manager and a file database.
        
        Args:
            api_key_manager (APIKeyManager): An instance of the APIKeyManager class for managing API keys.
            file_database (fileDatabase): An instance of the fileDatabase class for managing files.
        """
        self.api_key_manager = api_key_manager
        self.file_database = file_database
        
        self.processing_thread_running = True
        self.processingQueue = [] #this is a list of all the files that are being processed by the orchestrator
        self.processing_wakeup = threading.Condition()
        self.processing_thread = threading.Thread(target=self.process_files, daemon=True)
        self.processing_thread.start()
        
    def process_files(self):
        """
        Processes files in the processing queue. This method runs in a separate thread.
        """
        while self.processing_thread_running:
            with self.processing_wakeup:
                print("processing thread going to sleep!")
                while not self.processingQueue and self.processing_thread_running:
                    self.processing_wakeup.wait()
                
                
                while(self.processingQueue and self.processing_thread_running):
                    try:
                        file = heapq.heappop(self.processingQueue)
                        if(file.function == self.FileObject.Functions.ADD_FILE):
                            self.__add_file(file.URL, file.folderID, description=file.description)
                        elif(file.function == self.FileObject.Functions.GET_SUMMARY):
                            self.__summarize_external_file(URL=file.URL, fileID=file.fileID)
                    except Exception as e:
                        print(f"Error processing file: {e}")
        
    class FileObject:
        def __init__(self, function: int, priority: int, URL: str = None, folderID: int = None, fileID: int = None, description: str = None):
            """
            Initializes a FileObject
            
            Args:
                URL (str): The path to the file.
                folderID (int): The ID of the folder to which the file belongs.
                fileID (int): The ID of the file in the database.
            """
            self.URL = URL
            self.folderID = folderID
            self.fileID = fileID
            self.function = function
            self.priority = priority
            self.description = description
        
        #need to overload the less than comparator for the priority queue
        def __lt__(self, other):
            return self.priority < other.priority
    
        
        class Functions(enum.Enum):
            ADD_FILE = 1
            GET_SUMMARY = 2
        
    
        
    def queue_add_file(self, URL: str, folderID: int, description: str = None):
        """
        Adds an external file to the database and associates it with an API key.
        
        Args:
            URL (str): The path to the file to be added.
            APIKeyManager (APIKeyManager): An instance of the APIKeyManager class for managing API keys.
            fileDatabase (fileDatabase): An instance of the fileDatabase class for managing files.
            folderID (int): The ID of the folder to which the file will be added.
            
        Returns:
            bool: True if the file was successfully added, False otherwise.
        """
        file = self.FileObject(self.FileObject.Functions.ADD_FILE, priority=1, URL=URL, folderID=folderID, fileID=None, description=description)
        
        heapq.heappush(self.processingQueue, file)
        with self.processing_wakeup:
            self.processing_wakeup.notify()
    
    
    def __add_file(self, URL, folderID, description: str):
        service_requestor = requestors.get_requestor(URL) #check if the URL is valid and get the requestor for the service
        
        #check if any of our API keys have access to the file
        file = service_requestor.check_access(URL, self.api_key_manager)
        if(file):
            #if we can access the file, add it to the database
            fileID = self.file_database.add_file(name=file[1]['name'], folder_id=folderID, url=URL, description=description)
            if not description:
                file = self.FileObject(fileID=fileID, function=self.FileObject.Functions.GET_SUMMARY, priority=1)
                
                heapq.heappush(self.processingQueue, file)
                self.processing_wakeup.notify()
        else:
            raise ValueError(f"Could not access file {URL} with any of the API keys.")

    def __summarize_external_file(self, URL: str, fileID: int):
        """
        Summarizes an external file and adds it to the database.
        
        Args:
            URL (str): The path to the file to be summarized.
            APIKeyManager (APIKeyManager): An instance of the APIKeyManager class for managing API keys.
            fileDatabase (fileDatabase): An instance of the fileDatabase class for managing files.
            folderID (int): The ID of the folder to which the file will be added.
            
        Returns:
            bool: True if the file was successfully summarized, False otherwise.
        """
        if not URL:
            #get the URL from the database
            file = self.file_database.get_file(fileID)
            URL = file.URL
        
        service_requestor = requestors.get_requestor(URL)
        
        filename = service_requestor.download_external_file(URL=URL, API_db_manager=self.api_key_manager, filename=pathlib.Path("tempfile"))
        
        #summarize the file
        summary = AISummarizerService.summarize_from_external_service(filename)
        
        #save the summary
        self.file_database.update_file_summary(fileID, summary=summary)
    