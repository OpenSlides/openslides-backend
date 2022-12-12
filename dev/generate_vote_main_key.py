#tests imports
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64
# ende testimports
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import os
import sys
from typing import Tuple


PRIVATE_KEY_FILE = "vote_main_key"
PUBLIC_KEY_FILE = "public_vote_main_key"

def check_for_existence(path: str, filename: str) -> str:
    key_file = os.path.join(path, filename)
    if os.path.isfile(key_file):
        print(f"{key_file} exists! If you want to create a new one, delete the existing file!")
        sys.exit(1)
    return key_file

def generate_main_key() -> Tuple[bytes, bytes]:
    private_vote_main_key = Ed25519PrivateKey.generate()
    public_key = private_vote_main_key.public_key()
    private_bytes = private_vote_main_key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
    public_bytes = public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return (private_bytes, public_bytes)


def main() -> None:
    """
    Script generates the vote_main_key and it's public key

    """
    if len(sys.argv) < 2:
        print("call script with argument 'directory', where to save the main-key files." )
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.isdir(path):
        print(f"{path} is no directory. Create the directory, where to save the main-key files.")
        sys.exit(1)

    private_key_file = check_for_existence(path, PRIVATE_KEY_FILE)
    public_key_file = check_for_existence(path, PUBLIC_KEY_FILE)
    private_bytes, public_bytes = generate_main_key()
    with open(private_key_file, "wb") as keyfile:
        keyfile.write(private_bytes)
    with open(public_key_file, "wb") as keyfile:
        keyfile.write(public_bytes)


if __name__ == "__main__":
    main()
