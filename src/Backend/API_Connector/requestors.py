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
from urllib.parse import unquote
import base64

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
    def download_external_file(self, URL: str, API_db_manager: AccountDB.APIKeyManager, account: str | None, filename: Path):
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
                    f"https://www.googleapis.com/drive/v3/files/{file_id}?supportsAllDrives=true&fields=id,size,name,mimeType",
                    headers={
                        'Authorization': f'Bearer {accessToken}'
                    }
                )
                
                if response.status_code == 200:
                    #if the file is accessible, return True
                    return (accessToken, response.json())
            except Exception as e:
                # Log or handle the exception as needed
                print(f"An error occurred: {e}")
            
        return None
    
    @classmethod
    def download_external_file(cls, URL: str, API_db_manager: AccountDB.APIKeyManager, filename: Path):
        response = cls.check_access(URL, API_db_manager)
        
        #ask google if the file is accessible
        try:
            if response:
                file_size = response[1].get("size", 0)
                file_type = response[1].get("mimeType", "unknown")
                print(f"attempting to download {response[1].get('name')} with a detected type of {file_type}")
                
                #dont download more than 512 MB
                if(int(file_size) > 512 * 1024 * 1024):
                    raise ValueError("File is too large to summarize")
                else:
                    if(file_type == "application/vnd.google-apps.document"):
                        download_response = cls.googleOAuth.get(
                            f"https://docs.google.com/document/d/{response[1].get('id')}/export?format=pdf",
                            headers={
                                'Authorization': f'Bearer {response[0]}'
                            },
                            stream=True
                        )
                        filename = filename.with_suffix(f".pdf")
                    elif(file_type == "application/vnd.google-apps.spreadsheet"):
                        download_response = cls.googleOAuth.get(
                            f"https://docs.google.com/spreadsheets/d/{response[1].get('id')}/export?format=pdf",
                            headers={
                                'Authorization': f'Bearer {response[0]}'
                            },
                            stream=True
                        )
                        filename = filename.with_suffix(f".pdf")
                    elif(file_type == "application/vnd.google-apps.presentation"):
                        download_response = cls.googleOAuth.get(
                            f"https://docs.google.com/presentation/d/{response[1].get('id')}/export/pdf",
                            headers={
                                'Authorization': f'Bearer {response[0]}'
                            },
                            stream=True
                        )
                        filename = filename.with_suffix(f".pdf")
                    elif(file_type == "application/pdf"):
                        download_response = cls.googleOAuth.get(
                            f"https://www.googleapis.com/drive/v3/files/{response[1].get('id')}?alt=media",
                            headers={
                                'Authorization': f'Bearer {response[0]}'
                            },
                            stream=True
                        )
                        filename = filename.with_suffix(f".pdf")
                    elif(file_type.startswith("text/")):
                        download_response = cls.googleOAuth.get(
                            f"https://www.googleapis.com/drive/v3/files/{response[1].get('id')}?alt=media",
                            headers={
                                'Authorization': f'Bearer {response[0]}'
                            },
                            stream=True
                        )
                        filename = filename.with_suffix(f".txt")
                    else:
                        raise ValueError("File type not supported for automatic summarizing")
                    

                    if download_response.status_code == 200:
                        #save the file to a temporary location
                        with open(filename, "wb") as temp_file:
                            print(f"saving {URL} to {filename}")
                            for chunk in download_response.iter_content(chunk_size=8192):
                                temp_file.write(chunk)
                        
                        return filename
                    else:
                        raise ValueError("Failed to download the file")
                
        except Exception as e:
            # Log or handle the exception as needed
            print(f"An error occurred while downloading file: {e}")
            
        return None

class oneDriveRequestor(APIRequestor):
    service_name = "OneDrive"
    service_hostname = "onedrive.com"

    client_ID = r"77225b40-605d-45b7-822b-f8a1530691f6"
    scope = [r"Files.Read", r"openid"]
    base_authorization_url = r"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    token_url = r"https://login.microsoftonline.com/common/oauth2/v2.0/token"

    oneDriveOAuth = OAuth2Session(
        client_id=client_ID,
        redirect_uri=redirect_uri,
        scope=scope
    )

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

        # start local server
        global authorization_response
        authorization_response = None
        server_thread = threading.Thread(target=start_local_server)
        server_thread.start()
        authorization_url, _ = cls.oneDriveOAuth.authorization_url(
            cls.base_authorization_url,
            prompt="consent",
        )
        webbrowser.open(authorization_url)

        server_thread.join(30)

        if authorization_response is None:
            raise ValueError("Authorization response not received. Please try again.")

        full_redirect_uri = redirect_uri[:-1] + authorization_response

        token = cls.oneDriveOAuth.fetch_token(
            token_url=cls.token_url,
            authorization_response=full_redirect_uri,
            include_client_id=True,
            client_id=cls.client_ID
        )
        
        account_id = token.get("id_token") or token.get("access_token")
        if "id_token" in token:
            account_id = JWT().decode(token["id_token"], do_verify=False).get("sub")

        API_db_manager.store_api_key(key_name, account_id, cls.service_name, pickle.dumps(token))


    @classmethod
    def check_access(cls, URL: str, API_db_manager: AccountDB.APIKeyManager):
        if not URL:
            return False

        keys = API_db_manager.retrieve_api_keys_by_service("OneDrive")
        if not keys:
            print("No OneDrive API keys available.")
            return False

        for key in keys:
            token = pickle.loads(key[1])
            oneDriveOAuth = SafeOAuth2Session(client_id=cls.client_ID, token=token)

            # check if its a shared link
            try:
                # Check if the URL is a shared link
                share_id = base64.urlsafe_b64encode(URL.encode()).decode().rstrip("=")
                share_endpoint = f"https://graph.microsoft.com/v1.0/shares/u!{share_id}/driveItem?select=name,id,file"

                response = oneDriveOAuth.get(share_endpoint)
                if response.status_code == 200:
                    return (token, response.json())
            except Exception as e:
                print(f"Shared link access failed: {e}")

            # If not a shared link, check if it's a file path or ID
            try:
                path = urlparse(URL).path
                path = unquote(path.strip("/"))

                # Check whether it's a path or a file ID
                if "/" in path or "." in path:  # Likely a path like /Documents/test.pdf
                    endpoint = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}?select=name,id,file"
                else:  # Likely an ID
                    endpoint = f"https://graph.microsoft.com/v1.0/me/drive/items/{path}?select=name,id,file"

                response = oneDriveOAuth.get(endpoint)
                if response.status_code == 200:
                    return (token, response.json())
                else:
                    print(f"Fallback access failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error trying fallback access: {e}")

        return None

    @classmethod
    def download_external_file(cls, URL: str, API_db_manager: AccountDB.APIKeyManager, filename: Path):
        response = cls.check_access(URL, API_db_manager)

        try:
            if response:
                file_metadata = response[1]
                token = response[0].get('access_token')
                file_id = file_metadata.get("id")
                file_name = file_metadata.get("name")
                file_type = file_metadata.get("file", {}).get("mimeType", "unknown")
                print(f"Attempting to download {file_name} with detected type: {file_type}")

                # Check if the file is a PowerPoint file
                if file_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
                    # Export PowerPoint file as PDF
                    download_response = cls.oneDriveOAuth.get(
                        f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content?format=pdf",
                        headers={
                            'Authorization': f'Bearer {token}'
                        },
                        stream=True
                    )
                    filename = filename.with_suffix(".pdf")
                else:
                    # Default behavior: Download the file as-is
                    download_response = cls.oneDriveOAuth.get(
                        f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content",
                        headers={
                            'Authorization': f'Bearer {token}'
                        },
                        stream=True
                    )

                # Save the file
                if download_response.status_code == 200:
                    with open(filename, "wb") as temp_file:
                        print(f"Saving {file_name} to {filename}")
                        for chunk in download_response.iter_content(chunk_size=8192):
                            temp_file.write(chunk)
                    return filename
                else:
                    raise ValueError(f"Failed to download the file: {download_response.status_code} - {download_response.text}")

        except Exception as e:
            print(f"An error occurred while downloading the file: {e}")

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
    '1drv.ms': oneDriveRequestor,
    'onedrive.live.com': oneDriveRequestor,
    'microsoft.com': oneDriveRequestor
}
