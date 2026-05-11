import psycopg
import logging
import os
import requests
import json
import base64

from ..action import Action

logger = logging.getLogger(__name__)

class KeycloakMixin(Action):
    """
    Provides a mixin for keycloak
    """

    def get_config(key, default=""):
        return os.getenv(key, default)

    admin_username="admin"
    admin_password="admin"

    db_host = get_config("DATABASE_HOST")
    db_port = get_config("DATABASE_PORT")
    db_database = get_config("DATABASE_NAME")
    db_user = get_config("DATABASE_USER")
    db_password = get_config("DATABASE_PASSWORD")

    keycloak_url = get_config("KEYCLOAK_URL_INTERNAL", "http://keycloak-server:8080")
    keycloak_realm = get_config("KEYCLOAK_OS_REALM", "openslides")

    keycloak_admin_route = f"{keycloak_url}/admin/realms/{keycloak_realm}/"

    _keycloak_admin_key = ""

    def _get_admin_key(self):
        if self._keycloak_admin_key != "":
            return self._keycloak_admin_key

        # Fetch key if empty
        try:
            response = requests.post(f"{self.keycloak_url}/realms/master/protocol/openid-connect/token",
                data={
                    'client_id': "admin-cli",
                    'username': self.admin_username,
                    'password': self.admin_password,
                    'grant_type': "password",
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            json_response = response.json()

            if response.status_code != 200:
                raise Exception(f"{response.status_code} {json_response}")

            self._keycloak_admin_key = json_response["access_token"]
            return self._keycloak_admin_key
        except Exception as e:
            logger.error(f"Error receiving keycloak admin token: {e}")
        return ""

    def create_user(self, user, plaintext_password):
        keycloak_admin_key = self._get_admin_key()

        username = user["username"]
        email = user["email"]
        keycloak_id = user["keycloak_id"]

        if keycloak_id is None or keycloak_id == "":
            # No Keycloak ID set. This OS User likely has no Keycloak Account yet
            try:
                ## Upload OS user to Keycloak
                response = requests.post(self.keycloak_admin_route + "users",
                    json={
                        'username': username,
                        'email': email,
                        'enabled': True,
                    },
                    headers={
                        'Authorization': f'Bearer {keycloak_admin_key}',
                    }
                )

                if response.status_code == 201:
                    keycloak_id = response.headers.get('Location').split('/')[-1]
                elif response.status_code == 409:
                    raise Exception(f"A user named {username} already exists in keycloak.")
                elif keycloak_id == None:
                    raise Exception(f"ID returned by keycloak is empty")
            except Exception as e:
                logger.error(f"Error creating user: {e}")

        else:
            # A Keycloak ID already exists.
            # TODO: Should this be an error? What's to do here?
            raise Exception(f"Error creating user {username} in keycloak: They already have a keycloak ID")

        ## Update passowrd
        self.update_password(keycloak_id, plaintext_password)

        ## Set
        user['keycloak_id'] = keycloak_id


    def delete_user(self, user, keycloak_id):
        keycloak_admin_key = self._get_admin_key()

        ## Unset keycloak id
        user['keycloak_id'] = None

        try:
            ## Delete OS user from Keycloak
            response = requests.delete(self.keycloak_admin_route + "users/" + keycloak_id,
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )
            if response.status_code != 204:
                raise Exception(f"{response.json()}")
        except Exception as e:
            logger.error(f"Error deleting user: {e}")



    def update_user(self, keycloak_id, password, email):
        self.update_email(keycloak_id, email)
        self.update_password(keycloak_id, password)

    def update_email(self, keycloak_id, email):
        keycloak_admin_key = self._get_admin_key()

        # TODO

    # This adds '=' for argon2 padding at the end of a password or salt. It needs to pad until the length of the string is divisible by 4
    def hash_padding(self, to_pad):
        return to_pad + '=' * (-len(to_pad) % 4)

    def update_password(self, keycloak_id, plaintext_password):
        # Prepare Password. An argon2 encrypted password is expected
        hashed_password = self.auth.hash(plaintext_password)

        keycloak_admin_key = self._get_admin_key()

        try:
            response = requests.put(self.keycloak_admin_route + "users/" + keycloak_id,
                json={
                    'credentials' : [{
                        'type': 'password',
                        'credentialData': json.dumps({
                            'algorithm': 'argon2',
                            'hashIterations': 3,
                            'additionalParameters': {
                                'type': ['id'],
                                'version': ['1.3'],
                                'hashLength': ['32'],
                                'memory': ['65536'],
                                'parallelism': ['4'],
                            }
                        }),
                        'secretData': json.dumps({
                            'value': self.hash_padding(hashed_password.split('$')[5]),
                            'salt': self.hash_padding(hashed_password.split('$')[4]),
                        }),
                    }]
                },
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )

            if response.status_code != 204:
                raise Exception(f"{response.status_code} {response.json()}")
        except Exception as e:
            logger.error(f"Error migrating password for keycloak user {keycloak_id}: {e}")

