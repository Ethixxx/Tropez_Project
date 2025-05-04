from Backend.API_Connector import requestors
from Backend.API_Key_Container.AccountDB import APIKeyManager
from Backend.FileDatabase.database import fileDatabase

from urllib import parse

def add_external_file(URL: str, APIKeyManager: APIKeyManager, fileDatabase: fileDatabase, folderID: int):
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
    # Check if the URL is a string
    if not isinstance(URL, str):
        raise TypeError("URL must be a string")
    
    #get the hostname of the url
    parsed_url = parse.urlparse(URL).netloc
    if not parsed_url or len(parsed_url.split('.')) < 2:
        raise ValueError("Invalid URL")
    
    #get the top level domain (www.drive.google.com -> google.com)
    parsed_url = ".".join(parsed_url.split('.')[-2:])
    
    #check if the URL is supported by our requestors
    if(not parsed_url in requestors.supported_services_url):
        raise ValueError("service is not supported yet")

    #get the requestor class for the detected service
    service_requestor = requestors.supported_services_url[parsed_url]
    
    #check if any of our API keys have access to the file
    file = service_requestor.check_access(URL, APIKeyManager)
    if(file):
        #if we can access the file, add it to the database
        fileDatabase.add_file(name=file[1]['name'], folder_id=folderID, url=URL)

    return False
    
    