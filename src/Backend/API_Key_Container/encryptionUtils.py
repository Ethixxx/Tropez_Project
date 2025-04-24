#Defines a class of generic encryption and decryption methods


from abc import ABC, abstractmethod #for interfaces
from os import urandom #cryptographically secure RNG
from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV #AES in GCM-SIV mode
from cryptography.exceptions import InvalidTag #exception handling

#TODO: Make this cross-platform
from win32crypt import CryptUnprotectData, CryptProtectData #Windows Data Protection API


class encryptionUtils(ABC):
    #encrypts data using the master key
    #returns (cypherText, salt) on success
    #returns None on fail
    @abstractmethod
    def encrypt_with_auth(self, plainText: bytes, encryptedMasterKey: bytes):
        pass
    
    #decrypts and autheticates cypherText
    #returns plainText on success
    #returns None on fail
    @abstractmethod
    def decrypt_with_auth(self, cypherText: bytes, salt: bytes, encryptedMasterKey: bytes):
        pass
    
    #returns an encrypted master key that works with the cypher method
    @abstractmethod
    def generateMasterKey(self, description=None):
        pass
    
#an encryption utility class that uses the AES-GCM-SIV Encryption Mode
class AESGCMSIVInterface(encryptionUtils):
    def encrypt_with_auth(self, plainText: bytes, encryptedMasterKey: bytes):
        #decrypt the master key using windows data protection API
        decryptedMasterKey = CryptUnprotectData(encryptedMasterKey, None, None, None, 0)[1]
        
        #create a cipher with the master key
        cipher = AESGCMSIV(decryptedMasterKey)
        del decryptedMasterKey
        
        #generate a random salt
        salt = urandom(12)
        
        #encrypt the data
        try:
            cypherText = cipher.encrypt(salt, plainText, None)
        except OverflowError:
            return None
        
        #return tuple
        return (cypherText, salt)
    
    def decrypt_with_auth(self, cypherText: bytes, salt: bytes, encryptedMasterKey: bytes):
        #decrypt the master key using windows data protection API
        decryptedMasterKey = CryptUnprotectData(encryptedMasterKey, None, None, None, 0)[1]
        
        #create a cipher with the master key
        cipher = AESGCMSIV(decryptedMasterKey)
        del decryptedMasterKey
        
        #decrypt the data
        try:
            plainText = cipher.decrypt(salt, cypherText, None)
        except InvalidTag:
            return None
        
        return plainText
    
    def generateMasterKey(self, description=None):
        #generate the master key
        decryptedMasterKey = AESGCMSIV.generate_key(256)
        
        #encrypt the master key using windows data protection API
        encryptedMasterKey = CryptProtectData(decryptedMasterKey, description, None, None, None, 0)
        del decryptedMasterKey
        
        #return the encrypted master key
        return encryptedMasterKey