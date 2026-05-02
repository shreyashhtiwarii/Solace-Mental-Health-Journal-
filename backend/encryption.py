import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Generate a new key if one doesn't exist in environment.
# In production, ENCRYPTION_KEY MUST be set in .env securely.
# To generate a valid key, run: Fernet.generate_key()
_ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not _ENCRYPTION_KEY:
    _ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
    print("WARNING: No ENCRYPTION_KEY found in environment. Using an ephemeral key.")

fernet = Fernet(_ENCRYPTION_KEY.encode('utf-8'))

def encrypt_content(content: str) -> str:
    """Encrypts plaintext journal content into ciphertext."""
    if not content:
        return content
    return fernet.encrypt(content.encode('utf-8')).decode('utf-8')

def decrypt_content(ciphertext: str) -> str:
    """Decrypts ciphertext back into plaintext journal content."""
    if not ciphertext:
        return ciphertext
    try:
        return fernet.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return "⚠️ [Encrypted Content Unavailable]"
