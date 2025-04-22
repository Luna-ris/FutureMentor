import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

def generate_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key

def encrypt_data(data: str, password: str) -> str:
    salt = os.urandom(16)
    key = generate_key(password, salt)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded_data = data + " " * (16 - len(data) % 16)
    encrypted_data = encryptor.update(padded_data.encode()) + encryptor.finalize()
    return base64.b64encode(salt + iv + encrypted_data).decode()

def decrypt_data(encrypted_data: str, password: str) -> str:
    raw_data = base64.b64decode(encrypted_data.encode())
    salt = raw_data[:16]
    iv = raw_data[16:32]
    encrypted_data = raw_data[32:]
    key = generate_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    return decrypted_data.decode().rstrip()
