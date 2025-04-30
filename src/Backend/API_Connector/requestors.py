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

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


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
class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_response
        authorization_response = self.path
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Authorization successful. You can close this window.")
        print("Authorization response received.") 
    
#local http server to capture the authorization response
def start_local_server():
    server = HTTPServer(('localhost', 8443), OAuthHandler)
    server.handle_request()  # handle a single request and exit

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
    
    
#google drive integration
class GoogleDriveRequestor(APIRequestor):
    def __init__(self):
        super().__init__()
        self.client_ID = r"390769709576-9ge3uljai3a9fpm7lmhhkdm4rcafaoq3.apps.googleusercontent.com"
        self.scope = [r'https://www.googleapis.com/auth/drive.readonly']
        self.base_authorization_url = r'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_url = r'https://oauth2.googleapis.com/token'
        
        self.client_secret = None
        secret_path = Path(__file__).resolve().parent.parent.parent / "Backend" / "API_Connector" /'client_secret.txt'
        with open(secret_path, 'r') as f:
            self.client_secret = f.read().strip()
        
    def load_token_with_name(self, key_name, API_db_manager):
        #this method loads the token from the database and returns it
        #it returns None if the token is not found or if it is expired
        API_key = API_db_manager.retrieve_api_key_by_name(key_name)
        
        if API_key is None:
            return None
        
        if API_key[0] != "Google Drive":
            raise ValueError("Key already exists, but is not for Google Drive")
        
        #retrieve the token from the data
        token = pickle.loads(API_key[1])
        return token
        
        
    #this method is used to authenticate with the service and get an access token
    def get_token(self, key_name: str, API_db_manager: AccountDB.APIKeyManager):
        token = self.load_token_with_name(key_name, API_db_manager)
        if token: #don't create a new token if it already exists
            return
        
        
        googleOAuth = SafeOAuth2Session(
            client_id=self.client_ID,
            redirect_uri=redirect_uri,
            scope=self.scope,
        )
        
        authorization_url, state = googleOAuth.authorization_url(
            self.base_authorization_url,
            access_type="offline",
            prompt="consent")
        
        global authorization_response
        authorization_response = None
        
        server_thread = threading.Thread(target=start_local_server)
        server_thread.start()
        
        #open the webbrowser for the user to authenticate
        webbrowser.open(authorization_url)
        
        server_thread.join(30)
        if(authorization_response is None):
            raise ValueError("Authorization response not received. Please try again.")
        
        full_redirect_uri = redirect_uri[:-1] + authorization_response
        token = googleOAuth.fetch_token(
            self.token_url,
            authorization_response=full_redirect_uri,
            client_id=self.client_ID,
            include_client_id=True,
            client_secret=self.client_secret
        )
        
        #save the key
        API_db_manager.store_api_key(key_name, "Google Drive", pickle.dumps(token))

class oneDriveRequestor(APIRequestor):
    def __init__(self):
        super().__init__()
        self.client_ID = r"50d8f110-4943-4b84-a680-d4cb5040b262"
        self.scope = [r"https://graph.microsoft.com/Files.Read", "offline_access"]
        self.base_authorization_url = r"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        self.token_url = r"https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        self.client_secret = None
        secret_path = Path(__file__).resolve().parent.parent.parent / "Backend" / "API_Connector" / 'onedrive_client_secret.txt'
        with open(secret_path, 'r') as f:
            self.client_secret = f.read().strip()

    def load_token_with_name(self, key_name, API_db_manager):
        API_key = API_db_manager.retrieve_api_key_by_name(key_name)
        
        if API_key is None:
            return None
        
        if API_key[0] != "OneDrive":
            raise ValueError("Key already exists, but is not for OneDrive")
        
        token = pickle.loads(API_key[1])
        return token
    
    def get_token(self, key_name: str, API_db_manager: AccountDB.APIKeyManager):
        token = self.load_token_with_name(key_name, API_db_manager)
        if token:
            return

        oneDriveOAuth = SafeOAuth2Session(
            client_id=self.client_ID,
            redirect_uri=redirect_uri,
            scope=self.scope
        )

        authorization_url, state = oneDriveOAuth.authorization_url(
            self.base_authorization_url,
            access_type="offline",
            prompt="consent")
        
        global authorization_response
        authorization_response = None

        server_thread = threading.Thread(target=start_local_server)
        server_thread.start()
        webbrowser.open(authorization_url)
        server_thread.join(30)

        if authorization_response is None:
            raise ValueError("Authorization response not received. Please try again.")

        full_redirect_uri = redirect_uri[:-1] + authorization_response

        token = oneDriveOAuth.fetch_token(
            self.token_url,
            authorization_response=full_redirect_uri,
            client_id=self.client_ID,
            include_client_id=True,
            client_secret=self.client_secret
        )

        API_db_manager.store_api_key(key_name, "OneDrive", pickle.dumps(token))