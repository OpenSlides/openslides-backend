from os import environ

import requests
from keycloak import KeycloakAdmin

from .interface import IdpAdminService
from ..shared.authenticated_service import AuthenticatedService
from ...http.token_storage import token_storage
from ...shared.interfaces.logging import LoggingModule

ARGON2_HASH_START = "$argon2"
SHA512_HASHED_LENGTH = 152

class CustomKeycloakAdmin(KeycloakAdmin):
    def set_user_password_hash(self, user_id, hashed_password, algorithm="argon2", additional_params: dict = None):
        update_url = f"{self.server_url}/admin/realms/{self.realm_name}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.token['access_token']}",
            "Content-Type": "application/json"
        }
        credentials = {
            "type": "password",
            "hashedSaltedValue": hashed_password,
            "algorithm": algorithm,
            "temporary": False
        }
        if additional_params:
            credentials.update(additional_params)

        payload = {"credentials": [credentials]}
        response = requests.put(update_url, json=payload, headers=headers)
        if response.status_code == 204:
            print("Passwort-Hash erfolgreich gesetzt.")
        else:
            raise Exception(f"Fehler: {response.status_code}, {response.text}")

class MigrationKeycloakAdminAdapter(IdpAdminService, AuthenticatedService):
    """
    Adapter to connect keycloak getting admin credentials from environment variables.
    """

    def __init__(self, logging: LoggingModule | None = None) -> None:
        keycloak_url = environ.get("OPENSLIDES_KEYCLOAK_URL")
        keycloak_admin_username = environ.get("OPENSLIDES_KEYCLOAK_ADMIN_USERNAME")
        keycloak_admin_password = environ.get("OPENSLIDES_KEYCLOAK_ADMIN_PASSWORD")
        keycloak_realm_name = environ.get("OPENSLIDES_AUTH_REALM")
        self.keycloak_admin = CustomKeycloakAdmin(server_url=keycloak_url, username=keycloak_admin_username, password=keycloak_admin_password, realm_name=keycloak_realm_name)
        self.logger = logging.getLogger(__name__) if logging else None

class KeycloakAdminAdapter(IdpAdminService, AuthenticatedService):
    """
    Adapter to connect keycloak.
    """

    def __init__(self, keycloak_url: str, logging: LoggingModule) -> None:
        self.url = keycloak_url
        self.logger = logging.getLogger(__name__) if logging else None

    def create_keycloak_admin(self):
        access_token = token_storage.access_token
        keycloak_realm_name = environ.get("OPENSLIDES_AUTH_REALM")
        return CustomKeycloakAdmin(server_url=self.url, token=access_token, realm_name=keycloak_realm_name)

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
            algorithm = "sha512"
            additional_parameters = None
        else:
            algorithm = "argon2"
            additional_parameters = {
                "type": "argon2id",
                "version": "0x13",
                "hashLength": 32,
                "memory": 65536,
                "parallelism": 4,
                "iterations": 3
            }

        keycloak_admin = self.create_keycloak_admin()
        user_id = keycloak_admin.create_user({"username": username})
        keycloak_admin.set_user_password_hash(user_id, password_hash, algorithm, additional_parameters)
        if saml_id:
            keycloak_admin.update_user({"id": user_id, "attributes": {"saml_id": saml_id}})
        return user_id

    def is_sha512_hash(self, hash: str) -> bool:
        return (
                not hash.startswith(ARGON2_HASH_START) and len(hash) == SHA512_HASHED_LENGTH
        )

    def is_argon2_hash(self, hash: str) -> bool:
        return hash.startswith(ARGON2_HASH_START)