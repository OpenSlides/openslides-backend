import logging
import os
import requests
import json

from ..action import Action
from openslides_backend.shared.exceptions import ActionException

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
                raise ActionException(f"{response.status_code} {json_response}")

            self._keycloak_admin_key = json_response["access_token"]
            return self._keycloak_admin_key
        except Exception as e:
            raise ActionException(f"Error receiving keycloak admin token: {e}")
        return ""

    def find_and_remove_similar_keycloak_users(self, user):
        ## Finds keycloak users that share the same identifying keys in Keycloak and deletes them
        keycloak_admin_key = self._get_admin_key()

        # Database Key - Keycloak Query
        identifyingKeys = [["id", "q=os_id:{0}"], ["username", "username={0}"]]

        try:
            for idKey in identifyingKeys:
                ## Construct query
                query = idKey[1].format(str(user[idKey[0]]))

                self.logger.error(self.keycloak_admin_route + "users?" + query + "&exact=true")
                ## Find OS User
                response = requests.get(self.keycloak_admin_route + "users?" + query + "&exact=true&briefRepresentation=false",
                    headers={
                        'Authorization': f'Bearer {keycloak_admin_key}',
                    }
                )
                json_response = response.json()

                if response.status_code != 200:
                    raise ActionException(f"{response.status_code} {json_response}")

                if len(json_response) == 0:
                    # User does not exist
                    continue

                if not 'id' in json_response[0]:
                    raise ActionException(f"No id in Keycloak JSON response: {json_response}")

                self.delete_keycloak_user(json_response[0]['id'])
        except Exception as e:
            raise ActionException(f"Error finding user: {e}")

    # Gets keycloak id of given instance from the datastore
    def get_keycloak_id_from_datastore(self, instance) -> str:
        return self.datastore.get(
                fqid=f"user/{instance.get('id')}",
                mapped_fields=["keycloak_id"]
                )["keycloak_id"]

    def create_user(self, user, password = ""):
        keycloak_admin_key = self._get_admin_key()

        os_id = user["id"]
        username = user["username"]
        email = user["email"]
        keycloak_id = user.get("keycloak_id")

        if keycloak_id is None or keycloak_id == "":
            # No Keycloak ID set. This OS User likely has no Keycloak Account yet

            # Check if there is already a Keycloak User with the identifying keys and delete those accounts
            self.find_and_remove_similar_keycloak_users(user)

            try:
                ## Upload OS user to Keycloak
                response = requests.post(self.keycloak_admin_route + "users",
                    json={
                        'username': username,
                        'email': email,
                        'enabled': True,
                        "attributes": {
                            "os_id": os_id
                        },
                    },
                    headers={
                        'Authorization': f'Bearer {keycloak_admin_key}',
                    }
                )
                if response.status_code == 201:
                    keycloak_id = response.headers.get('Location').split('/')[-1]
                elif response.status_code == 409:
                    raise ActionException(f"A user named {username} already exists in keycloak.")
                elif keycloak_id == None:
                    raise ActionException(f"ID returned by keycloak is empty")
            except Exception as e:
                raise ActionException(f"Error creating user: {e}")

        else:
            # A Keycloak ID already exists.
            # TODO: Should this be an error? What's to do here?
            raise ActionException(f"Error creating user {username} in keycloak: They already have a keycloak ID")

        ## Update passowrd
        if password is not None and password != "":
            self.update_keycloak_password(keycloak_id, password)

        ## Set
        user['keycloak_id'] = keycloak_id

    # Deletes the keycloak user belonging to the given os user.
    # Warning: This will not remove the keycloak_id from the os user in the database!
    def delete_user(self, instance):
        self.delete_keycloak_user(self.get_keycloak_id_from_datastore(instance))

    def delete_keycloak_user(self, keycloak_id):
        if keycloak_id is None or keycloak_id == "":
            self.logger.error(f"Deleting keycloak user couldn't be done: no keycloak ID")
            return

        keycloak_admin_key = self._get_admin_key()

        try:
            ## Logout user
            self.logout_keycloak_user(keycloak_id)

            ## Delete OS user from Keycloak
            response = requests.delete(self.keycloak_admin_route + "users/" + keycloak_id,
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error deleting user: {e}")

    # Logs user out and thereby revokes any active session of user
    def logout_user(self, instance):
        self.logout_keycloak_user(self.get_keycloak_id_from_datastore(instance))

    def logout_keycloak_user(self, keycloak_id):

        if keycloak_id is None or keycloak_id == "":
            self.logger.error(f"Logout of keycloak user couldn't be done: no keycloak ID")
            return

        keycloak_admin_key = self._get_admin_key()

        try:
            ## Logout user
            response = requests.post(self.keycloak_admin_route + "users/" + keycloak_id + "/logout",
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {json_response}")

        except Exception as e:
            raise ActionException(f"Error logout of user: {e}")

    # Enables or disables login access in keycloak for the user
    def set_user_enable_status(self, instance, enabled):
        self.set_keycloak_user_enable_status(self.get_keycloak_id_from_datastore(instance), enabled)

    def set_keycloak_user_enable_status(self, keycloak_id, enabled):
        if keycloak_id is None or keycloak_id == "":
            self.logger.error(f"Setting enable status of keycloak user couldn't be done: no keycloak ID")
            return

        if not isinstance(enabled, bool):
            self.logger.error(f"Setting enable status of keycloak user couldn't be done: enabled parameter not a bool")
            return

        keycloak_admin_key = self._get_admin_key()

        try:
            ## Change enable status of Keycloak user
            response = requests.put(self.keycloak_admin_route + "users/" + keycloak_id,
                json={
                    'enabled': enabled,
                },
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )
            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {json_response}")
        except Exception as e:
            raise ActionException(f"Error setting enable status of user: {e}")

    # Resets users password. User has to create new password. An email will be send with necessary information
    # User will be logged out
    def force_reset_password(self, instance):
        self.reset_keycloak_password(self.get_keycloak_id_from_datastore(instance))

    def force_reset_keycloak_password(self, keycloak_id):
        if not keycloak_id or keycloak_id == "":
            raise ActionException(f"Resetting password couldn't be done: no keycloak ID")

        keycloak_admin_key = self._get_admin_key()

        try:
            response = requests.put(self.keycloak_admin_route + "users/" + keycloak_id + "/execute-actions-email",
                json=[
                        'UPDATE_PASSWORD'
                    ]
                ,
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code}, {response.json()}")

            # Logout user
            self.logout_keycloak_user(keycloak_id)
        except Exception as e:
            raise ActionException(f"Error sending password reset email to user {keycloak_id}: {e}")

    # Updates email of user
    def update_email(self, instance, email):
        self.update_keycloak_email(self.get_keycloak_id_from_datastore(instance), email)

    def update_keycloak_email(self, keycloak_id, email):

        if keycloak_id is None or keycloak_id == "":
            self.logger.error(f"Updating email of keycloak user couldn't be done: no keycloak ID")
            return

        if email is None or email == "":
            self.logger.error(f"Updating email of keycloak user couldn't be done: no email")
            return

        keycloak_admin_key = self._get_admin_key()

        try:
            ## Change email of Keycloak user
            response = requests.put(self.keycloak_admin_route + "users/" + keycloak_id,
                json={
                    'email': email,
                },
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )
            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating email of user: {e}")
    
    # Updates username of user
    def update_username(self, instance, username):
        self.update_keycloak_username(self.get_keycloak_id_from_datastore(instance), username)

    def update_keycloak_username(self, keycloak_id, username):

        if keycloak_id is None or keycloak_id == "":
            self.logger.error(f"Updating username of keycloak user couldn't be done: no keycloak ID")
            return

        if username is None or username == "":
            self.logger.error(f"Updating username of keycloak user couldn't be done: no email")
            return

        keycloak_admin_key = self._get_admin_key()

        try:
            ## Change username of Keycloak user
            response = requests.put(self.keycloak_admin_route + "users/" + keycloak_id,
                json={
                    'username': username,
                },
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )
            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating username of user: {e}")
    
    # This adds '=' for argon2 padding at the end of a password or salt. It needs to pad until the length of the string is divisible by 4
    def hash_padding(self, to_pad):
        return to_pad + '=' * (-len(to_pad) % 4)

    def update_password(self, instance, password):
        self.update_keycloak_password(self.get_keycloak_id_from_datastore(instance), password)

    def update_keycloak_password(self, keycloak_id, password):
        if not keycloak_id or keycloak_id == "":
            raise ActionException(f"Updating password couldn't be done: no keycloak ID")

        # An argon2 encrypted password is expected
        if not password.startswith("$argon2"):
            raise ActionException(f"Password of keycloak user {keycloak_id} is not argon2-encrypted: {password}")

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
                            'value': self.hash_padding(password.split('$')[5]),
                            'salt': self.hash_padding(password.split('$')[4]),
                        }),
                    }]
                },
                headers={
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating password for keycloak user directly {keycloak_id}: {e}")

