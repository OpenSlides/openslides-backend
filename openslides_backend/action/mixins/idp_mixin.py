import logging
import os
import requests
import json
import base64

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

    admin_token_path = "/zitadel/bootstrap/admin.pat"
    organization_id_path = "/zitadel/bootstrap/org-id"

    db_host = get_config("DATABASE_HOST")
    db_port = get_config("DATABASE_PORT")
    db_database = get_config("DATABASE_NAME")
    db_user = get_config("DATABASE_USER")
    db_password = get_config("DATABASE_PASSWORD")

    external_host = get_config("IDP_EXTERNAL_HOST", "localhost:8800")

    idp_route = get_config("IDP_URL_INTERNAL", "http://zitadel-api:8080")
    idp_realm = get_config("IDP_OS_REALM", "openslides")

    idp_admin_route = f"{idp_route}/v2/"

    _idp_admin_access_token = ""
    _idp_organisation_id = ""

    def _get_admin_key(self):
        if self._idp_admin_access_token != "":
            return self._idp_admin_access_token

        # Fetch key from admin file
        try:
            with open(self.admin_token_path) as file:
                self._idp_admin_access_token = file.read().replace("\n","")
                return self._idp_admin_access_token
        except Exception as e:
            raise ActionException(f"Error reading admin pat file: {e}")

    def _get_organisation_id(self):
        if self._idp_organisation_id != "":
            return self._idp_organisation_id

        # Fetch key from organization file
        try:
            with open(self.organization_id_path) as file:
                self._idp_organisation_id = file.read().replace("\n","")
                return self._idp_organisation_id
        except Exception as e:
            raise ActionException(f"Error reading organization id file: {e}")

    # Gets IDP id of given instance from the datastore
    def get_idp_id_from_datastore(self, instance) -> str:
        try:
            return self.datastore.get(
                fqid=f"user/{instance.get('id')}",
                mapped_fields=["idp_id"]
                )["idp_id"]
        except Exception as e:
            return ""


    def find_and_remove_similar_idp_users(self, user):
        ## Finds IDP users that share the same identifying keys in IDP and deletes them
        idp_admin_access_token = self._get_admin_key()

        try:
            response = requests.post(self.idp_admin_route + "users",
                json={
                    'queries':
                    [
                        {
                            'orQuery': {
                                'queries': [
                                    {
                                        'loginNameQuery': {
                                            'loginName': user['username'],
                                            'method': 'TEXT_QUERY_METHOD_EQUALS',
                                        }
                                    },
                                    {
                                        'andQuery': {
                                            'queries': [
                                                {
                                                    'metadataKeyFilter': {
                                                        'key': 'os-id',
                                                        'method': 'TEXT_FILTER_METHOD_EQUALS',
                                                    },
                                                },
                                                {
                                                    'metadataValueFilter': {
                                                        'value': base64.b64encode(str(user['id']).encode("utf-8")).decode("ascii"),
                                                        'method': 'BYTE_FILTER_METHOD_EQUALS',
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                ]
                            }
                        }
                    ]
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )

            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {response.text}")

            json_response = response.json()

            if "result" not in json_response or "totalResult" not in json_response["details"] or json_response["details"]["totalResult"] <= 0:
                # User does not exist
                return

            found_users = json_response['result']

            logger.warning(f"--- {found_users}")
            for user in found_users:
                logger.warning(f"Found user: {user}")

                self.delete_user(user['id'])

        except Exception as e:
            raise ActionException(f"Error finding user: {e}")

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
                response = requests.post(self.idp_admin_route + "users/new",
                    json={
                        'username': username,
                        'organizationId': self._get_organisation_id(),
                        'human': {
                            'hashedPassword': {
                                'hash': password
                            },
                            'profile': {
                                'givenName': username,
                                'familyName': username,
                            },
                            'email': {
                                'email': email,
                                'isVerified': True
                            }
                        },
                        'metadata': [
                            {
                                'key': 'os_id',
                                'value': base64.b64encode(str(os_id).encode("utf-8")).decode("ascii")
                            },
                        ]
                    },
                    headers={
                        'Authorization': f'Bearer {idp_admin_access_token}',
                        'Host': f'{self.external_host}'
                    }
                )
                if response.status_code == 200:
                    idp_id = response.json()["id"]
                elif response.status_code == 409:
                    raise ActionException(f"A user named {username} already exists in IDP.")
                elif idp_id == None:
                    raise ActionException(f"ID returned by IDP is empty. Response: {response.json()}")
            except Exception as e:
                raise ActionException(f"Error creating user: {e}")

        else:
            # A OIDC ID already exists.
            # TODO: Should this be an error? What's to do here?
            raise ActionException(f"Error creating user {username} in IDP: They already have a IDP ID")

        ## Set
        user['idp_id'] = idp_id

    # Deletes the OIDC user belonging to the given os user.
    # Warning: This will not remove the idp_id from the os user in the database!
    def delete_user(self, instance):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if idp_id is None or idp_id == "":
            self.logger.error(f"Deleting IDP user couldn't be done: no IDP ID")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Logout user
            self.logout_user(idp_id)

            ## Delete OS user from IDP
            response = requests.delete(self.idp_admin_route + "users/" + idp_id,
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )

            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error deleting user: {e}")

    # Logs user out and thereby revokes any active session of user
    def logout_user(self, instance):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if idp_id is None or idp_id == "":
            self.logger.error(f"Logout of IDP user couldn't be done: no IDP ID")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            response = requests.post(self.idp_admin_route + "sessions/search",
                json={
                    'queries': [
                    {
                        'userIdQuery': {
                            'id': idp_id
                        }
                    }
                ]
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )

            logger.warning(f"Testing logut: {response.json()}")
            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {json_response}")

            for session in response.json()["sessions"]:
                logger.warning(f"Testing logut specific session: {session}")
                response = requests.delete(self.idp_admin_route + "sessions/" + session["id"],
                    json={},
                    headers={
                        'Authorization': f'Bearer {idp_admin_access_token}',
                        'Host': f'{self.external_host}'
                    }
                )

                if response.status_code != 200:
                    raise ActionException(f"{response.status_code} {json_response}")

        except Exception as e:
            raise ActionException(f"Error logout of user: {e}")

    # Enables or disables login access in IDP for the user
    def set_user_enable_status(self, instance, enabled):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if idp_id is None or idp_id == "":
            self.logger.error(f"Setting enable status of IDP user couldn't be done: no IDP ID")
            return

        if not isinstance(enabled, bool):
            self.logger.error(f"Setting enable status of IDP user couldn't be done: enabled parameter not a bool")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            if enabled:
                command = "deactivate"
            else:
                command = "reactivate"

            ## Change enable status of IDP user
            response = requests.post(self.idp_admin_route + "users/" + idp_id + "/" + command,
                json={
                    'enabled': enabled,
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )
            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {json_response}")
        except Exception as e:
            raise ActionException(f"Error setting enable status of user: {e}")

    # Resets users password. User has to create new password. An email will be send with necessary information
    # User will be logged out
    def force_reset_password(self, instance):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id or idp_id == "":
            raise ActionException(f"Resetting password couldn't be done: no IDP ID")

        idp_admin_access_token = self._get_admin_key()

        try:
            response = requests.post(self.idp_admin_route + "users/" + idp_id + "/password_reset",
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )

            if response.status_code != 200:
                raise ActionException(f"{response.status_code}, {response.json()}")

            # Logout user
            self.logout_user(idp_id)
        except Exception as e:
            raise ActionException(f"Error sending password reset email to user {idp_id}: {e}")

    # Updates email of user
    def update_email(self, instance, email):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if idp_id is None or idp_id == "":
            self.logger.error(f"Updating email of IDP user couldn't be done: no IDP ID")
            return

        if email is None or email == "":
            self.logger.error(f"Updating email of IDP user couldn't be done: no email")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Change email of IDP user
            response = requests.patch(self.idp_admin_route + "users",
                json={
                    'human': {
                        'email': {
                            'email': email,
                            'isVerified': True
                        }
                    }
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )
            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating email of user: {e}")

    # Updates username of user
    def update_username(self, instance, username):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if idp_id is None or idp_id == "":
            self.logger.error(f"Updating username of IDP user couldn't be done: no IDP ID")
            return

        if username is None or username == "":
            self.logger.error(f"Updating username of IDP user couldn't be done: no email")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            ## Change username of IDP user
            response = requests.patch(self.idp_admin_route + "users",
                json={
                    'username': username
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )
            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating username of user: {e}")

    # This adds '=' for argon2 padding at the end of a password or salt. It needs to pad until the length of the string is divisible by 4
    def hash_padding(self, to_pad):
        return to_pad + '=' * (-len(to_pad) % 4)

    def update_password(self, instance, password):
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id or idp_id == "":
            raise ActionException(f"Updating password couldn't be done: no IDP ID")

        # An argon2 encrypted password is expected
        if not password.startswith("$argon2"):
            raise ActionException(f"Password of IDP user {idp_id} is not argon2-encrypted: {password}")

        idp_admin_access_token = self._get_admin_key()

        try:

            ## Change email of IDP user
            response = requests.patch(self.idp_admin_route + "users",
                json={
                    'human': {
                        'hashedPassword': {
                            'hash': password
                        }
                    }
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )
            """
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
            )"""

            if response.status_code != 200:
                raise ActionException(f"{response.status_code} {response.json()}")
        except Exception as e:
            raise ActionException(f"Error updating password for IDP user directly {idp_id}: {e}")

