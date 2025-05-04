from sqlalchemy import create_engine, Column, String, LargeBinary, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from Backend.API_Key_Container.encryptionUtils import AESGCMSIVInterface

APIBase = declarative_base()

class APIKey(APIBase):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True) #unique identifier per api key
    name = Column(String, nullable=False, unique=True) #user inputed name for this api key
    account = Column(String, nullable=False, unique=True) #identifier for the account this key belongs to
    service = Column(String, nullable=False) #service name for use in the request type lookup table
    encrypted_key = Column(LargeBinary, nullable=False)
    salt = Column(LargeBinary, nullable=False)

class Secrets(APIBase):
    __tablename__ = 'secrets'
    key = Column(String, primary_key=True, unique=True)  # Generic key column
    value = Column(LargeBinary, nullable=False)  # Generic value column (BLOB)

class APIKeyManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        APIBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        self.encryptor = AESGCMSIVInterface()

        # Ensure a master key exists
        self._initialize_master_key()

    def _initialize_master_key(self):
        session = self.Session()
        existing_key = session.query(Secrets).filter_by(key="API_Master_Key").first()
        if existing_key:
            self.master_key = existing_key.value
        else:
            self.master_key = self.encryptor.generateMasterKey()
            new_secret = Secrets(key="API_Master_Key", value=self.master_key)
            session.add(new_secret)
            session.commit()
        session.close()

    #this method is used to securely encrypt and store new api keys
    def store_api_key(self, name, account, service, api_key):
        encrypted_data = self.encryptor.encrypt_with_auth(api_key.encode(), self.master_key)
        if encrypted_data:
            session = self.Session()
            
            #detect if name is not new
            existing_key = session.query(APIKey).filter_by(name=name).first()
            if not existing_key:
                new_key = APIKey(name=name, service=service, account=account, encrypted_key=encrypted_data[0], salt=encrypted_data[1])
                session.add(new_key)
                session.commit()
            session.close()
    
    #this method is used to change an api key's name
    def rename_api_key(self, id, new_name):
        session = self.Session()
        #if the new name doesnt already exist
        existing_key = session.query(APIKey).filter_by(name=new_name).first()
        if not existing_key:
            key_entry = session.query(APIKey).filter_by(id=id).first()
            if key_entry:
                key_entry.name = new_name
                session.commit()
        session.close()
    
    #this method is used to securely encrypt and change an existing api key
    def change_api_key(self, id, new_key):
        encrypted_data = self.encryptor.encrypt_with_auth(new_key, self.master_key)
        if encrypted_data:
            session = self.Session()
            key_entry = session.query(APIKey).filter_by(id=id).first()
            if key_entry:
                key_entry.encrypted_key = encrypted_data[0]
                key_entry.salt = encrypted_data[1]
                session.commit()
            session.close()
            
    #this method is used to delete an api key
    def delete_api_key(self, id):
        session = self.Session()
        key_entry = session.query(APIKey).filter_by(id=id).first()
        if key_entry:
            session.delete(key_entry)
            session.commit()
        session.close()
    
    #this method lists api keys for a specific service
    def list_api_keys(self, service):
        session = self.Session()
        key_entries = session.query(APIKey).filter_by(service=service).distinct()
        keys = [(key_entry.id, key_entry.name) for key_entry in key_entries]
        session.close()
        return keys

    #this method lists all services with api key(s)
    def list_services(self):
        session = self.Session()
        services = session.query(APIKey.service).distinct()
        session.close()
        return (service[0] for service in services)
    
    #this method lists all api keys
    def list_all_api_keys(self: int) -> list[tuple[int, str]]:
        session = self.Session()
        key_entries = session.query(APIKey).all()
        keys = [(key_entry.id, key_entry.name) for key_entry in key_entries]
        session.close()
        return keys

    #this method is used to find and decrypt an api key entry from its id for use in upper levels
    def retrieve_api_key_by_id(self, id: int) -> tuple[str, bytes]:
        session = self.Session()
        key_entry = session.query(APIKey).filter_by(id=id).first()
        if key_entry:
            encrypted_key = key_entry.encrypted_key
            salt = key_entry.salt
            decrypted_key = (key_entry.service,self.encryptor.decrypt_with_auth(encrypted_key, salt, self.master_key))
            if decrypted_key[1]:
                return decrypted_key
        session.close()
        return None
    
    def retrieve_api_keys_by_service(self, service) -> list[tuple[int, bytes]]:
        session = self.Session()
        key_entries = session.query(APIKey).filter_by(service=service).all()
        keys = []
        for key_entry in key_entries:
            decrypted_key = (key_entry.id,self.encryptor.decrypt_with_auth(key_entry.encrypted_key, key_entry.salt, self.master_key))
            if decrypted_key[1]:
                keys.append(decrypted_key)
        
        return keys
        
    #this method is used to find and decrypt an api key entry from its name for use in upper levels
    def retrieve_api_key_by_name(self, name: str) -> tuple[str, bytes]:
        session = self.Session()
        key_entry = session.query(APIKey).filter_by(name=name).first()
        if key_entry:
            encrypted_key = key_entry.encrypted_key
            salt = key_entry.salt
            decrypted_key = (key_entry.service,self.encryptor.decrypt_with_auth(encrypted_key, salt, self.master_key))
            if decrypted_key[1]:
                return decrypted_key
        session.close()
        return None
    
    def retrieve_id_with_account_and_service(self, account: str, service: str) -> int:
        session = self.Session()
        key_entry = session.query(APIKey).filter_by(account=account, service=service).first()
        if key_entry:
            return key_entry.id
        session.close()
        return None
    
# Example usage:
if __name__ == "__main__":

    db_url = 'sqlite:///api_keys.db'
    manager = APIKeyManager(db_url)
    
    # Store an API key
    manager.store_api_key('Main Github','GitHub', b'ghp_example123')  # Use bytes object
    
    # Retrieve an API key
    api_key = manager.retrieve_api_key_by_name('Main Github')
