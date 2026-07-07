import logging
import os
import requests
import json

from ..action import Action
from openslides_backend.shared.exceptions import ActionException

logger = logging.getLogger(__name__)

class IDPMixin(Action):
    """
    Provides a mixin for an external Identity Provider
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

    idp_route = get_config("IDP_URL_INTERNAL", "http://zitadel-api:8080")
    idp_realm = get_config("IDP_OS_REALM", "openslides")

    idp_admin_route = f"{idp_route}/admin/realms/{idp_realm}/"

    _idp_admin_access_token = ""

    def _get_admin_key(self):
        if self._idp_admin_access_token != "":
            return self._idp_admin_access_token

        # Fetch key if empty
        try:
            response = requests.post(f"{self.idp_route}/realms/master/protocol/openid-connect/token",
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

            self._idp_admin_access_token = json_response["access_token"]
            return self._idp_admin_access_token
        except Exception as e:
            raise ActionException(f"Error receiving idp admin token: {e}")
        return ""

    def find_and_remove_similar_idp_users(self, user):
        ## Finds IDP users that share the same identifying keys in IDP and deletes them
        idp_admin_access_token = self._get_admin_key()

        # Database Key - IDP Query
        identifyingKeys = [["id", "q=os_id:{0}"], ["username", "username={0}"]]

        try:
            for idKey in identifyingKeys:
                ## Construct query
                query = idKey[1].format(str(user[idKey[0]]))

                ## Find OS User
                response = requests.get(self.idp_admin_route + "users?" + query + "&exact=true&briefRepresentation=false",
                    headers={
                        'Authorization': f'Bearer {idp_admin_access_token}',
                    }
                )
                json_response = response.json()

                if response.status_code != 200:
                    raise ActionException(f"{response.status_code} {json_response}")

                if len(json_response) == 0:
                    # User does not exist
                    continue

                if not 'id' in json_response[0]:
                    raise ActionException(f"No id in IDP JSON response: {json_response}")

                self.delete_idp_user(json_response[0]['id'])
        except Exception as e:
            raise ActionException(f"Error finding user: {e}")

    # Gets IDP id of given instance from the datastore
    def get_idp_id_from_datastore(self, instance) -> str:
        try:
            return self.datastore.get(
                fqid=f"user/{instance.get('id')}",
                mapped_fields=["idp_id"]
                )["idp_id"]
        except Exception as e:
            return ""


    def create_user(self, user, password = ""):
        idp_admin_access_token = self._get_admin_key()

        os_id = user["id"]
        username = user["username"]
        email = user["email"]
        idp_id = user.get("idp_id")

        if idp_id is None or idp_id == "":
            # No IDP ID set. This OS User likely has no IDP Account yet

            # Check if there is already a IDP User with the identifying keys and delete those accounts
            self.find_and_remove_similar_idp_users(user)

            try:
                ## Upload OS user to IDP
                response = requests.post(self.idp_admin_route + "users",
                    json={
                        'username': username,
                        'email': email,
                        'enabled': True,
                        "attributes": {
                            "os_id": os_id
                        },
                    },
                    headers={
                        'Authorization': f'Bearer {idp_admin_access_token}',
                    }
                )
                if response.status_code == 201:
                    idp_id = response.headers.get('Location').split('/')[-1]
                elif response.status_code == 409:
                    raise ActionException(f"A user named {username} already exists in IDP.")
                elif idp_id == None:
                    raise ActionException(f"ID returned by IDP is empty")
            except Exception as e:
                raise ActionException(f"Error creating user: {e}")

        else:
            # A OIDC ID already exists.
            # TODO: Should this be an error? What's to do here?
            raise ActionException(f"Error creating user {username} in IDP: They already have a IDP ID")

        ## Update passowrd
        if password is not None and password != "":
            self.update_idp_password(idp_id, password)

        ## Set
        user['idp_id'] = idp_id

    # Deletes the OIDC user belonging to the given os user.
    # Warning: This will not remove the idp_id from the os user in the database!
    def delete_user(self, instance):
        self.delete_idp_user(self.get_idp_id_from_datastore(instance))

    def delete_idp_user(self, idp_id):
        if idp_id is None or idp_id == "":
            self.logger.error(f"Deleting IDP user couldn't be done: no IDP ID")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Logout user
            self.logout_idp_user(idp_id)

            ## Delete OS user from IDP
            response = requests.delete(self.idp_admin_route + "users/" + idp_id,
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error deleting user: {e}")

    # Logs user out and thereby revokes any active session of user
    def logout_user(self, instance):
        self.logout_idp_user(self.get_idp_id_from_datastore(instance))

    def logout_idp_user(self, idp_id):

        if idp_id is None or idp_id == "":
            self.logger.error(f"Logout of IDP user couldn't be done: no IDP ID")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Logout user
            response = requests.post(self.idp_admin_route + "users/" + idp_id + "/logout",
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {json_response}")

        except Exception as e:
            raise ActionException(f"Error logout of user: {e}")

    # Enables or disables login access in IDP for the user
    def set_user_enable_status(self, instance, enabled):
        self.set_idp_user_enable_status(self.get_idp_id_from_datastore(instance), enabled)

    def set_idp_user_enable_status(self, idp_id, enabled):
        if idp_id is None or idp_id == "":
            self.logger.error(f"Setting enable status of IDP user couldn't be done: no IDP ID")
            return

        if not isinstance(enabled, bool):
            self.logger.error(f"Setting enable status of IDP user couldn't be done: enabled parameter not a bool")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Change enable status of IDP user
            response = requests.put(self.idp_admin_route + "users/" + idp_id,
                json={
                    'enabled': enabled,
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                }
            )
            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {json_response}")
        except Exception as e:
            raise ActionException(f"Error setting enable status of user: {e}")

    # Resets users password. User has to create new password. An email will be send with necessary information
    # User will be logged out
    def force_reset_password(self, instance):
        self.reset_idp_password(self.get_idp_id_from_datastore(instance))

    def force_reset_idp_password(self, idp_id):
        if not idp_id or idp_id == "":
            raise ActionException(f"Resetting password couldn't be done: no IDP ID")

        idp_admin_access_token = self._get_admin_key()

        try:
            response = requests.put(self.idp_admin_route + "users/" + idp_id + "/execute-actions-email",
                json=[
                        'UPDATE_PASSWORD'
                    ]
                ,
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code}, {response.json()}")

            # Logout user
            self.logout_idp_user(idp_id)
        except Exception as e:
            raise ActionException(f"Error sending password reset email to user {idp_id}: {e}")

    # Updates email of user
    def update_email(self, instance, email):
        self.update_idp_email(self.get_idp_id_from_datastore(instance), email)

    def update_idp_email(self, idp_id, email):

        if idp_id is None or idp_id == "":
            self.logger.error(f"Updating email of IDP user couldn't be done: no IDP ID")
            return

        if email is None or email == "":
            self.logger.error(f"Updating email of IDP user couldn't be done: no email")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Change email of IDP user
            response = requests.put(self.idp_admin_route + "users/" + idp_id,
                json={
                    'email': email,
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                }
            )
            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating email of user: {e}")

    # Updates username of user
    def update_username(self, instance, username):
        self.update_idp_username(self.get_idp_id_from_datastore(instance), username)

    def update_idp_username(self, idp_id, username):

        if idp_id is None or idp_id == "":
            self.logger.error(f"Updating username of IDP user couldn't be done: no IDP ID")
            return

        if username is None or username == "":
            self.logger.error(f"Updating username of IDP user couldn't be done: no email")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Change username of IDP user
            response = requests.put(self.idp_admin_route + "users/" + idp_id,
                json={
                    'username': username,
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
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
        self.update_idp_password(self.get_idp_id_from_datastore(instance), password)

    def update_idp_password(self, idp_id, password):
        if not idp_id or idp_id == "":
            raise ActionException(f"Updating password couldn't be done: no IDP ID")

        # An argon2 encrypted password is expected
        if not password.startswith("$argon2"):
            raise ActionException(f"Password of IDP user {idp_id} is not argon2-encrypted: {password}")

        idp_admin_access_token = self._get_admin_key()

        try:
            response = requests.put(self.idp_admin_route + "users/" + idp_id,
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
                    'Authorization': f'Bearer {idp_admin_access_token}',
                }
            )

            if response.status_code != 204:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating password for IDP user directly {idp_id}: {e}")

