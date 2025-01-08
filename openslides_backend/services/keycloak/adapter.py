import base64
import json
from os import environ
import logging

import requests
from keycloak import KeycloakAdmin

from datastore.shared.di import service_as_singleton
from .interface import IdpAdminService
from ..shared.authenticated_service import AuthenticatedService
from ...http.token_storage import token_storage
from ...shared.interfaces.logging import LoggingModule

ARGON2_HASH_START = "$argon2"
SHA512_HASHED_LENGTH = 152

class CustomKeycloakAdmin(KeycloakAdmin):
    def set_user_password_hash(self, user_id, secret_data, credential_data):
        self.connection.realm_name = "os"
        print(f"Setting password hash for user {user_id}")
        update_url = f"{self.connection.server_url}/admin/realms/{self.connection.realm_name}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.connection.token['access_token']}",
            "Content-Type": "application/json"
        }
        credentials = {
            "type": "password",
            "secretData": json.dumps(secret_data),
            "credentialData": json.dumps(credential_data),
            "temporary": False,
        }
        payload = {"credentials": [credentials]}
        response = requests.put(update_url, json=payload, headers=headers)
        if response.status_code == 204:
            print("Passwort-Hash erfolgreich gesetzt.")
        else:
            raise Exception(f"Fehler: {response.status_code}, {response.text}")

@service_as_singleton
class KeycloakAdminAdapter(IdpAdminService, AuthenticatedService):
    """
    Adapter to connect keycloak.
    """
    keycloak_admin_obj = None

    def __init__(self) -> None:
        keycloak_url = environ.get("OPENSLIDES_KEYCLOAK_URL")
        self.url = keycloak_url
        self.logger = logging.getLogger(__name__)

    def create_keycloak_admin(self):
        access_token = token_storage.access_token
        keycloak_realm_name = environ.get("OPENSLIDES_AUTH_REALM")
        print(f"Creating Keycloak admin with realm: {keycloak_realm_name} on {self.url}")
        return CustomKeycloakAdmin(server_url=self.url, token=access_token, realm_name=keycloak_realm_name)

    def keycloak_admin(self):
        if self.keycloak_admin_obj is None:
            self.keycloak_admin_obj = self.create_keycloak_admin()
        return self.keycloak_admin_obj

    def create_user(self, username: str, password_hash: str, saml_id: str | None) -> str:
        '''
        public static final String TYPE_KEY = "type";
        public static final String VERSION_KEY = "version";
        public static final String HASH_LENGTH_KEY = "hashLength";
        public static final String MEMORY_KEY = "memory";
        public static final String ITERATIONS_KEY = "iterations";
        public static final String PARALLELISM_KEY = "parallelism";

        Defaults in the argon2 npm package:
        type: argon2id
        version: 0x13
        hashLength: 32
        memory: 65536
        parallelism: 4
        iterations: 3
        '''
        if not self.is_sha512_hash(password_hash) and not self.is_argon2_hash(password_hash):
            raise ValueError("The password hash is not a valid hash.")
        if self.is_sha512_hash(password_hash):
            secret_data = {
                "value": password_hash
            }
            credential_data = {
                "algorithm": "sha512"
            }
        else:
            # example value: $argon2id$v=19$m=65536,t=3,p=4$ag1cK0W8DxJ6VnUlOdgRKQ$wi/8MnuLaOWZVhO/7p4N+XWgnh6S2qTnrDylY+Z/tQc
            hash_data = self.parse_argon2_hash(password_hash)
            secret_data = {
                "salt": password_hash.split("$")[4],
                "value": password_hash.split("$")[5]
            }
            parameters = password_hash.split("$")[3].split(",")
            credential_data = {
                "algorithm": "argon2",
                "additionalParameters": {
                    "type": hash_data["argon_type"],
                    # encode version as hexadecimal
                    "version": f"0x{hash_data['version']:02x}",
                    "hashLength": hash_data["hash_length"],
                    "memory": hash_data["parameters"]["m"],
                    "parallelism": hash_data["parameters"]["p"],
                    "iterations": hash_data["parameters"]["t"]
                }

            }
        print(f"Creating user {username} with password hash {password_hash}")
        keycloak_admin = self.keycloak_admin()
        existing_user_id = keycloak_admin.get_user_id(username)
        user_id = existing_user_id if existing_user_id else keycloak_admin.create_user({"username": username})
        keycloak_admin.set_user_password_hash(user_id, secret_data, credential_data)
        if saml_id:
            print(f"Setting saml_id {saml_id} for user {user_id}")
            keycloak_admin.update_user({"id": user_id, "attributes": {"saml_id": saml_id}})
        return user_id

    def parse_argon2_hash(argon2_hash):
        # Split the hash string into its components
        parts = argon2_hash.split('$')
        if len(parts) != 6:
            raise ValueError("Invalid Argon2 hash format.")

        # Extract the components
        argon_type = parts[1]  # e.g., "argon2id"
        version = parts[2][2:]  # e.g., "19" (remove "v=")
        parameters = parts[3]  # e.g., "m=65536,t=3,p=4"
        salt_base64 = parts[4]  # Base64 encoded salt
        hash_base64 = parts[5]  # Base64 encoded hash

        # Parse parameters into a dictionary
        param_dict = {}
        for param in parameters.split(','):
            key, value = param.split('=')
            param_dict[key] = int(value)

        # Decode the salt and hash
        salt = base64.b64decode(salt_base64 + "=" * ((4 - len(salt_base64) % 4) % 4))
        derived_hash = base64.b64decode(hash_base64 + "=" * ((4 - len(hash_base64) % 4) % 4))

        # Return parsed components
        return {
            "argon_type": argon_type,
            "version": int(version),
            "parameters": param_dict,
            "salt": salt_base64,
            "salt_length": len(salt),
            "hash": hash_base64,
            "hash_length": len(derived_hash)
        }


    def is_sha512_hash(self, hash: str) -> bool:
        return (
                not hash.startswith(ARGON2_HASH_START) and len(hash) == SHA512_HASHED_LENGTH
        )

    def is_argon2_hash(self, hash: str) -> bool:
        return hash.startswith(ARGON2_HASH_START)

@service_as_singleton
class MigrationKeycloakAdminAdapter(KeycloakAdminAdapter):
    """
    Adapter to connect keycloak getting admin credentials from environment variables.
    """
    def create_keycloak_admin(self):
        keycloak_realm_name = environ.get("OPENSLIDES_AUTH_REALM")
        keycloak_admin_username = environ.get("OPENSLIDES_KEYCLOAK_ADMIN_USERNAME")
        keycloak_admin_password = environ.get("OPENSLIDES_KEYCLOAK_ADMIN_PASSWORD")
        print(f"Creating Keycloak admin with realm: {keycloak_realm_name}, username: {keycloak_admin_username} on {self.url}, password: {keycloak_admin_password}")
        admin = CustomKeycloakAdmin(server_url="http://keycloak:8080/idp/", username="admin",
                                    password="admin", realm_name="master", client_id="admin-cli", verify=False)
        # admin.connection.realm_name = keycloak_realm_name
        return admin
