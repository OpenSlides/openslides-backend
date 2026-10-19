import base64
import logging
import os
from typing import Any

import requests
from requests import Response

from openslides_backend.shared.exceptions import ActionException

from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.write_request import WriteRequest
from ..action import Action

logger = logging.getLogger(__name__)


class IDPMixin(Action):
    """
    Provides a mixin for an external Identity Provider concerning user integration
    """

    admin_token_path = "/zitadel/bootstrap/admin.pat"
    organization_id_path = "/zitadel/bootstrap/org-id"

    external_host = os.getenv("IDP_EXTERNAL_HOST", "localhost:8800")

    idp_route = os.getenv("IDP_URL_INTERNAL", "http://zitadel-api:8080")

    idp_admin_route = f"{idp_route}/v2/"

    _idp_admin_access_token = ""
    _idp_organization_id = ""

    def _get_admin_key(self) -> str:
        if self._idp_admin_access_token != "":
            return self._idp_admin_access_token

        # Fetch key from admin file
        try:
            with open(self.admin_token_path) as file:
                self._idp_admin_access_token = file.read().replace("\n", "")
                return self._idp_admin_access_token
        except Exception as e:
            raise ActionException(f"Error reading admin pat file: {e}")

    def _get_organization_id(self) -> str:
        if self._idp_organization_id != "":
            return self._idp_organization_id

        # Fetch key from organization id file
        try:
            with open(self.organization_id_path) as file:
                self._idp_organization_id = file.read().replace("\n", "")
                return self._idp_organization_id
        except Exception as e:
            raise ActionException(f"Error reading organization id file: {e}")

    # Gets IDP id of given instance from the datastore
    def get_idp_id_from_datastore(self, instance: dict[str, Any]) -> str:
        try:
            return self.datastore.get(
                fqid=f"user/{instance.get('id')}", mapped_fields=["idp_id"]
            )["idp_id"]
        except Exception as e:
            self.logger.debug(f"No user found for {instance.get('id')}: {e}")
            return ""

    def find_and_remove_similar_idp_users(self, user: dict[str, Any]) -> None:
        # Finds IDP users that share the same identifying keys in IDP and deletes them
        idp_admin_access_token = self._get_admin_key()

        try:
            """
            response = requests.post(self.idp_admin_route + "users",
                json={
                    'queries':
                    [
                        {
                            'orQuery': {
                                'queries': [
                                    {
                                        'userNameQuery': {
                                            'userName': user['username'],
                                            'method': 'TEXT_QUERY_METHOD_EQUALS',
                                        }
                                    },
                                    {
                                        'andQuery': {
                                            'queries': [
                                                {
                                                    'metadataKeyFilter': {
                                                        'key': 'os_id',
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
                    ],
                    "query": {
                        "offset": 0,
                        "limit": 100
                    }
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_access_token}',
                    'Host': f'{self.external_host}'
                }
            )
            """

            response = requests.post(
                self.idp_admin_route + "users",
                json={
                    "queries": [
                        {
                            "userNameQuery": {
                                "userName": user["username"],
                            }
                        },
                    ],
                    "query": {"offset": 0, "limit": 100},
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )

            if response.status_code != 200:
                self.idp_error(response)

            json_response = response.json()

            if (
                "result" not in json_response
                or "totalResult" not in json_response["details"]
                or int(json_response["details"]["totalResult"]) <= 0
            ):
                # User does not exist
                return

            found_users = json_response["result"]

            for user_to_delete in found_users:
                self.delete_user(user_to_delete["userId"])

        except Exception as e:
            raise ActionException(f"Error finding user: {e}")

    def create_user(
        self, user: dict[str, Any], password: str, user_is_instance: bool
    ) -> None:
        idp_admin_access_token = self._get_admin_key()

        os_id = user.get("id")
        username = user.get("username")
        email = user.get("email")
        idp_id = user.get("idp_id")

        if not idp_id:
            # No IDP ID set. This OS User likely has no IDP Account yet
            # Check if there is already an IDP User with the identifying keys and delete those accounts
            self.find_and_remove_similar_idp_users(user)

            try:
                # Upload OS user to IDP
                response = requests.post(
                    self.idp_admin_route + "users/new",
                    json={
                        "username": username,
                        "organizationId": self._get_organization_id(),
                        "human": {
                            "hashedPassword": {"hash": password},
                            "profile": {
                                "givenName": username,
                                "familyName": username,
                            },
                            "email": {"email": email, "isVerified": True},
                        },
                        "metadata": [
                            {
                                "key": "os_id",
                                "value": base64.b64encode(
                                    str(os_id).encode("utf-8")
                                ).decode("ascii"),
                            },
                        ],
                    },
                    headers={
                        "Authorization": f"Bearer {idp_admin_access_token}",
                        "Host": f"{self.external_host}",
                    },
                )
                if response.status_code == 200:
                    idp_id = response.json()["id"]
                    if idp_id is None:
                        raise ActionException(
                            f"ID returned by IDP is empty. Response: {response.json()}"
                        )
                elif response.status_code == 409:
                    raise ActionException(
                        f"A user named {username} already exists in IDP."
                    )
                else:
                    raise ActionException(
                        f"ID returned by IDP is empty. Unexpected response: {response.text}"
                    )
            except Exception as e:
                raise ActionException(f"Error creating user: {e}")

        else:
            # An OIDC ID already exists.
            # TODO: Should this be an error? What's to do here?
            raise ActionException(
                f"Error creating user {username} in IDP: They already have an IDP ID"
            )

        # Write IDP ID in datastore
        if user_is_instance:
            user["idp_id"] = idp_id
        else:
            try:
                self.datastore.write(
                    WriteRequest(
                        events=[
                            Event(
                                type=EventType.Update,
                                fqid=f"user/{os_id}",
                                fields={
                                    "idp_id": idp_id,
                                },
                            )
                        ],
                        user_id=os_id,
                        locked_fields={},
                    )
                )
            except Exception as e:
                self.logger.warning(
                    "TODO: Causes initial import issues as user table does not exist yet"
                )
                raise ActionException(f"Error writing IPD ID in datastore: {e}")

    # Deletes the OIDC user belonging to the given os user.
    # Warning: This will not remove the idp_id from the os user in the database!
    def delete_user(self, instance: dict[str, Any]) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            self.logger.error("Deleting IDP user couldn't be done: no IDP ID")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            # Logout user
            self.revoke_all_sessions_of_user(idp_id)

            # Delete OS user from IDP
            response = requests.delete(
                self.idp_admin_route + "users/" + idp_id,
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )

            if response.status_code != 200 and response.status_code != 404:
                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error deleting user: {e}")

    # Logs user out and thereby revokes any active session of user
    def revoke_all_sessions_of_user(self, instance: str | dict[str, Any]) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            self.logger.error("Logout of IDP user couldn't be done: no IDP ID")
            return

        idp_admin_access_token = self._get_admin_key()
        self.logger.warning(f"Revoke sessions for {idp_id}")
        try:
            response = requests.post(
                self.idp_admin_route + "sessions/search",
                json={
                    "query": {"offset": 0, "limit": 100, "asc": True},
                    "queries": [
                        {"userIdQuery": {"id": f"{idp_id}"}},
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )
            if response.status_code != 200:
                self.idp_error(response)

            json_response = response.json()

            if "sessions" not in json_response:
                self.logger.warning("No session has been found")
                return

            for session in json_response["sessions"]:
                self.logger.warning(f"Removing Session: {session['id']}")
                response = requests.delete(
                    self.idp_admin_route + "sessions/" + session["id"],
                    json={},
                    headers={
                        "Authorization": f"Bearer {idp_admin_access_token}",
                        "Host": f"{self.external_host}",
                    },
                )

                if response.status_code != 200:
                    self.idp_error(response)

        except Exception as e:
            raise ActionException(f"Error logout of user: {e}")

    # Enables or disables login access in IDP for the user
    def set_user_enable_status(self, instance: dict[str, Any], enabled: bool) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            self.logger.error(
                "Setting enable status of IDP user couldn't be done: no IDP ID"
            )
            return

        if not isinstance(enabled, bool):
            self.logger.error(
                "Setting enable status of IDP user couldn't be done: enabled parameter not a bool"
            )
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            if not enabled:
                command = "deactivate"
            else:
                command = "reactivate"

            # Change enable status of IDP user
            response = requests.post(
                self.idp_admin_route + "users/" + idp_id + "/" + command,
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )
            if response.status_code != 200:
                if response.status_code == 400 and response.json()["code"] == 9:
                    self.logger.warning(
                        "User was supposed to be activated/deactivated, but was already active/inactive in IDP"
                    )
                    return

                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error setting enable status of user: {e}")

    # Resets users password. User has to create new password. An email will be sent with necessary information
    # User will be logged out
    def force_reset_password(self, instance: dict[str, Any]) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            raise ActionException("Resetting password couldn't be done: no IDP ID")

        idp_admin_access_token = self._get_admin_key()

        try:
            response = requests.post(
                self.idp_admin_route + "users/" + idp_id + "/password_reset",
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )

            if response.status_code != 200:
                raise ActionException(f"{response.status_code}, {response.json()}")

            # Logout user
            self.revoke_all_sessions_of_user(idp_id)
        except Exception as e:
            raise ActionException(
                f"Error sending password reset email to user {idp_id}: {e}"
            )

    # Updates email of user
    def update_email(self, instance: dict[str, Any], email: str) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            self.logger.error("Updating email of IDP user couldn't be done: no IDP ID")
            return

        if not email:
            self.logger.error("Updating email of IDP user couldn't be done: no email")
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            # Change email of IDP user
            response = requests.patch(
                self.idp_admin_route + "users/" + idp_id,
                json={"human": {"email": {"email": email, "isVerified": True}}},
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )
            if response.status_code != 200:
                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error updating email of user: {e}")

    # Updates username of user
    def update_username(self, instance: dict[str, Any], username: str) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            self.logger.error(
                "Updating username of IDP user couldn't be done: no IDP ID"
            )
            return

        if username is None or username == "":
            self.logger.error(
                "Updating username of IDP user couldn't be done: no username"
            )
            return

        idp_admin_access_token = self._get_admin_key()

        try:
            # Change username of IDP user
            response = requests.patch(
                self.idp_admin_route + "users/" + idp_id,
                json={"username": username, "human": {}},
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )
            if response.status_code != 200:
                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error updating username of user: {e}")

    # This adds '=' for argon2 padding at the end of a password or salt. It needs to pad until the length of the string is divisible by 4
    # def hash_padding(self, to_pad):
    #    return to_pad + "=" * (-len(to_pad) % 4)

    def update_password(
        self, instance: dict[str, Any], password: str, is_encrypted: bool
    ) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            raise ActionException("Updating password couldn't be done: no IDP ID")
        if not password:
            raise ActionException(
                "Updating password couldn't be done: password is empty"
            )

        # If password is encrypted, then it must be argon2 encrypted
        if is_encrypted and not password.startswith("$argon2"):
            raise ActionException("Password is not argon2-encrypted")

        idp_admin_access_token = self._get_admin_key()

        try:
            # Change password of IDP user
            json_payload = {
                "human": {"password": {"hashedPassword": {"hash": f"{password}"}}}
            }
            if not is_encrypted:
                json_payload = {
                    "human": {"password": {"password": {"password": f"{password}"}}}
                }

            response = requests.patch(
                self.idp_admin_route + "users/" + idp_id,
                json=json_payload,
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
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
                raise ActionException(f"Error updating password: {response.text}")

            # Logout user
            self.revoke_all_sessions_of_user(idp_id)

        except Exception as e:
            raise ActionException(f"Error updating password: {e}")

    def user_changes_password(
        self, instance: dict[str, Any], newPassword: str, oldPassword: str
    ) -> None:
        if isinstance(instance, str):
            idp_id = instance
        else:
            idp_id = self.get_idp_id_from_datastore(instance)

        if not idp_id:
            raise ActionException("Changing password couldn't be done: no IDP ID")

        idp_admin_access_token = self._get_admin_key()

        try:
            # Change password of IDP user
            response = requests.patch(
                self.idp_admin_route + "users/" + idp_id,
                json={
                    "human": {
                        "password": {
                            "password": {"password": f"{newPassword}"},
                            "currentPassword": f"{oldPassword}",
                        }
                    }
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
            )

            if response.status_code != 200:
                error_response = response.json()["message"]
                if "COMMAND-3M0fs" in error_response:
                    raise ActionException("Old password is not correct")
                else:
                    raise ActionException(f"Error updating password: {response.text}")

            # Logout user
            self.revoke_all_sessions_of_user(idp_id)
        except Exception as e:
            raise ActionException(f"Error changing password: {e}")

    # Throws a generic error to the client while logging the real issue
    def idp_error(self, from_response: Response) -> None:
        self.logger.error(f"{from_response.status_code} - {from_response.text}")
        raise ActionException(
            "An IDP error occurred. Please contact your administrator"
        )
