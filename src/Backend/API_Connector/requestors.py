from abc import ABC, abstractmethod #for interfaces
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
import pickle
from pathlib import Path
from Backend.API_Key_Container import AccountDB 

from requests_oauthlib import OAuth2Session
import webbrowser
from urllib.parse import urlparse
import os
from jwt import JWT

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from urllib import parse


#allow the oauth library to use http (subclassed to only allow localhost to use http)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
redirect_uri = r"http://localhost:8443/"

class SafeOAuth2Session(OAuth2Session):
    def request(self, method, url, *args, **kwargs):
        parsed = urlparse(url)

        # Allow HTTP only for localhost
        if parsed.scheme == 'http':
            if parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
                raise ValueError(f"Insecure transport to non-localhost address not allowed: {url}")

        return super().request(method, url, *args, **kwargs)

#handler for OAuth Callbacks
authorization_response = None
server_started = threading.Event()
class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_response
        authorization_response = self.path
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("""<html><head><title>Authorization</title><script>window.onload = function() {window.open('', '_self'); window.close();};</script></head><body><p>Authorization successful. You can close this window.</p></body></html>""".encode("utf-8"))
    
#local http server to capture the authorization response
def start_local_server():
    global redirect_uri
    global server_started
    for port in range (8443, 8500):
        try:
            server = HTTPServer(('localhost', port), OAuthHandler)
        except OSError as e:
            continue
        
        server_started.set()
        redirect_uri = f"http://localhost:{port}/"
        server.timeout = 30
        server.handle_request()  # handle a single request and exit
        break
        

#main interface for a class that uses OAuth 2.0 to authenticate with a service and make requests for files
class APIRequestor(ABC):
    def __init__(self):
        super().__init__()
        
    #this method is used to authenticate with the service and get an access token
    @abstractmethod
    def get_token(self, name: str, API_db_manager: AccountDB.APIKeyManager):
        pass
    
    @abstractmethod
    def load_token_with_name(self, key_name: str, API_db_manager: AccountDB.APIKeyManager):
        pass
    
    @abstractmethod
    def check_access(self, URL: str, API_db_manager: AccountDB.APIKeyManager) -> tuple[str, dict] | None:
        pass
    
    @abstractmethod
    def get_tokens_by_service(self, API_db_manager: AccountDB.APIKeyManager):
        pass
    
    @abstractmethod
    def download_external_file(self, URL: str, API_db_manager: AccountDB.APIKeyManager, account: str | None):
        pass
    
    
#google drive integration
class GoogleDriveRequestor(APIRequestor):
    service_name = "Google Drive"
    service_hostname = "google.com"
    
    client_ID = r"390769709576-9ge3uljai3a9fpm7lmhhkdm4rcafaoq3.apps.googleusercontent.com"
    scope = [r'https://www.googleapis.com/auth/drive.readonly', r'openid']
    base_authorization_url = r'https://accounts.google.com/o/oauth2/v2/auth'
    token_url = r'https://oauth2.googleapis.com/token'
    client_secret = os.getenv("GOOGLE_CLIENT_KEY") 
    
    googleOAuth = SafeOAuth2Session(
        client_id=client_ID,
        redirect_uri=redirect_uri,
        scope=scope,
    )
     
    @staticmethod
    def load_token_with_name(key_name, API_db_manager):
        #this method loads the token from the database and returns it
        #it returns None if the token is not found or if it is expired
        API_key = API_db_manager.retrieve_api_key_by_name(key_name)
        
        if API_key is None:
            return None
        
        if API_key[0] != "Google Drive":
            raise ValueError("Key exists, but is not for Google Drive")
        
        #retrieve the token from the data
        token = API_key[1]
        return token
        
        
    #this method is used to authenticate with the service and get an access token
    @classmethod
    def get_token(cls, key_name: str, API_db_manager: AccountDB.APIKeyManager):
        token = cls.load_token_with_name(key_name, API_db_manager)
    
        if token: #don't create a new token if it already exists
            raise ValueError("Token already exists")
        
        #start the local server to capture the authorization response
        server_thread = threading.Thread(target=start_local_server)
        server_thread.start()
        
        server_started.wait(5)
        
        authorization_url, __ = cls.googleOAuth.authorization_url(
            cls.base_authorization_url,
            access_type="offline",
            prompt="consent")
        
        global authorization_response
        authorization_response = None
                
        
        #open the webbrowser for the user to authenticate
        webbrowser.open(authorization_url)
        
        server_thread.join(20)
        if(authorization_response is None):
            raise ValueError("Authorization response not received. Please try again.")
        
        full_redirect_uri = redirect_uri[:-1] + authorization_response
        token = cls.googleOAuth.fetch_token(
            token_url=cls.token_url,
            authorization_response=full_redirect_uri,
            client_id=cls.client_ID,
            include_client_id=True,
            client_secret=cls.client_secret
        )
        
        authorization_response = None
        
        #get the user's unique account id
        account_id = JWT().decode(message=token.get("id_token"), do_verify=False).get("sub")
        
        #check if the user already has a key associated with their account
        existing_key = API_db_manager.retrieve_id_with_account_and_service(account_id, "Google Drive")
        if existing_key:
            #if the key already exists, update it
            API_db_manager.change_api_key(existing_key, token["refresh_token"])
            API_db_manager.rename_api_key(existing_key, key_name)
        else:
            #if the key does not exist, create it
            API_db_manager.store_api_key(key_name, account_id, "Google Drive", token["refresh_token"])
    
    @staticmethod
    def get_tokens_by_service(API_db_manager: AccountDB.APIKeyManager):
        return API_db_manager.retrieve_api_keys_by_service("Google Drive")
    
    @classmethod
    def check_access(cls, URL: str, API_db_manager: AccountDB.APIKeyManager):
        #check if the URL is a file link
        if "/d/" not in URL:
            return False
        
        #get the file id
        file_id = URL.split("/d/")[1].split("/")[0]
        
        keys = cls.get_tokens_by_service(API_db_manager)
        for key in keys:
            refreshToken = key[1]
            
            #generate an access token
            accessToken = cls.googleOAuth.refresh_token(
                                token_url='https://oauth2.googleapis.com/token',
                                refresh_token=refreshToken,
                                client_id=cls.client_ID,
                                client_secret=cls.client_secret
                            )
            
            
            #ask google if the file is accessible
            try:
                response = cls.googleOAuth.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}?supportsAllDrives=true",
                    headers={
                        'Authorization': f'Bearer {accessToken}'
                    }
                )
                
                if response.status_code == 200:
                    #if the file is accessible, return True
                    return (key[0], response.json())
            except Exception as e:
                # Log or handle the exception as needed
                print(f"An error occurred: {e}")
            
        return None
    
    @classmethod
    def download_external_file(cls, URL: str, API_db_manager: AccountDB.APIKeyManager, account: str):
        #get the hostname of the url
        parsed_url = parse.urlparse(URL).netloc
        if not parsed_url or len(parsed_url.split('.')) < 2:
            raise ValueError("Invalid URL")
        
        #get the top level domain (www.drive.google.com -> google.com)
        parsed_url = ".".join(parsed_url.split('.')[-2:])

        #check if the URL is a file link
        if "/d/" not in URL or parsed_url.lower() != "google.com":
            return False
        
        #get the file id
        file_id = URL.split("/d/")[1].split("/")[0]
        
        if(isinstance(account, str)):
            key = API_db_manager.retrieve_id_with_account_and_service(account, "Google Drive")
            
        #generate an access token
        accessToken = cls.googleOAuth.refresh_token(
                            token_url='https://oauth2.googleapis.com/token',
                            refresh_token=key[1],
                            client_id=cls.client_ID,
                            client_secret=cls.client_secret
                        )
        
        
        #ask google if the file is accessible
        try:
            response = cls.googleOAuth.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}?supportsAllDrives=true",
                headers={
                    'Authorization': f'Bearer {accessToken}'
                }
            )
            
            if response.status_code == 200:
                #if the file is accessible, download it 
                file_metadata = response.json()
                file_size = file_metadata.get("size", 0)
                
                #dont download more than 512 MB
                if(file_size > 512 * 1024 * 1024):
                    raise ValueError("File is too large to summarize")
                else:
                    download_response = cls.googleOAuth.get(
                        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
                        headers={
                            'Authorization': f'Bearer {accessToken}'
                        },
                        stream=True
                    )
                    
                    if download_response.status_code == 200:
                        #save the file to a temporary location
                        temp_file_path = Path("temp_file")
                        with open(temp_file_path, "wb") as temp_file:
                            for chunk in download_response.iter_content(chunk_size=8192):
                                temp_file.write(chunk)
                        
                        return temp_file_path
                    else:
                        raise ValueError("Failed to download the file")
                
        except Exception as e:
            # Log or handle the exception as needed
            print(f"An error occurred: {e}")
            
        return None

class oneDriveRequestor(APIRequestor):
    service_name = "OneDrive"
    service_hostname = "onedrive.com"

    client_ID = r"50d8f110-4943-4b84-a680-d4cb5040b262"
    scope = [r"https://graph.microsoft.com/Files.Read", "offline_access"]
    base_authorization_url = r"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    token_url = r"https://login.microsoftonline.com/common/oauth2/v2.0/token"
    client_secret = os.getenv("ONEDRIVE_CLIENT_KEY") 

    @classmethod
    def load_token_with_name(cls, key_name: str, API_db_manager: AccountDB.APIKeyManager):
        API_key = API_db_manager.retrieve_api_key_by_name(key_name)

        if API_key is None:
            return None

        if API_key[0] != cls.service_name:
            raise ValueError(f"Key exists, but is not for {cls.service_name}")

        token = pickle.loads(API_key[1])
        return token

    @classmethod
    def get_token(cls, key_name: str, API_db_manager: AccountDB.APIKeyManager):
        token = cls.load_token_with_name(key_name, API_db_manager)
        if token:
            raise ValueError("Token already exists")

        oneDriveOAuth = SafeOAuth2Session(
            client_id=cls.client_ID,
            redirect_uri=redirect_uri,
            scope=cls.scope
        )

        # start local server
        global authorization_response
        authorization_response = None
        server_thread = threading.Thread(target=start_local_server)
        server_thread.start()
        webbrowser.open(oneDriveOAuth.authorization_url(
            cls.base_authorization_url,
            access_type="offline",
            prompt="consent"
        )[0])

        server_thread.join(30)

        if authorization_response is None:
            raise ValueError("Authorization response not received. Please try again.")

        full_redirect_uri = redirect_uri[:-1] + authorization_response

        token = oneDriveOAuth.fetch_token(
            token_url=cls.token_url,
            authorization_response=full_redirect_uri,
            client_id=cls.client_ID,
            include_client_id=True,
            client_secret=cls.client_secret
        )

        # store the token in the database
        API_db_manager.store_api_key(key_name, cls.service_name, token["refresh_token"])

    @classmethod
    def check_access(cls, URL: str, API_db_manager: AccountDB.APIKeyManager):
        # onedrive-specific url validation
        if "onedrive.live.com" not in URL:
            return False
        
        keys = API_db_manager.retrieve_api_keys_by_service("OneDrive")
        for key in keys:
            token = pickle.loads(key[1])
            oneDriveOAuth = SafeOAuth2Session(
                client_id=cls.client_ID,
                token=token
            )

            try:
                response = oneDriveOAuth.get(
                    "https://graph.microsoft.com/v1.0/me/drive/root/children",  # example endpoint
                    headers={'Authorization': f'Bearer {token["access_token"]}'}
                )

                if response.status_code == 200:
                    return (key[0], response.json())
            except Exception as e:
                print(f"Error accessing OneDrive file: {e}")
        
        return None

def get_requestor(URL: str) -> APIRequestor:
    """
    Returns the appropriate requestor class based on the URL.
    
    Args:
        URL (str): The URL to check.
        
    Returns:
        APIRequestor: The appropriate requestor class.
        
    Raises:
        ValueError: If the URL does not match any supported services.
    """
    if not isinstance(URL, str):
        raise TypeError("URL must be a string")
    
    parsed_url = parse.urlparse(URL).netloc
    if not parsed_url or len(parsed_url.split('.')) < 2:
        raise ValueError("Invalid URL")
    
    #get the top level domain (www.drive.google.com -> google.com)
    parsed_url = ".".join(parsed_url.split('.')[-2:])
    
    if parsed_url in supported_services_url:
        return supported_services_url[parsed_url]
    
    raise ValueError("service is not supported yet")

supported_services = {
    'Google Drive': GoogleDriveRequestor,
    'OneDrive': oneDriveRequestor
}
supported_services_url = {
    'google.com': GoogleDriveRequestor,
    'live.com': oneDriveRequestor,
    'microsoft.com': oneDriveRequestor
}
