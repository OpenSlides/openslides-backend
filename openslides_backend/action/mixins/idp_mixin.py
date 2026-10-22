import logging
import os
from typing import Any
import requests

from openslides_backend.shared.exceptions import ActionException
from ..action import Action

logger = logging.getLogger(__name__)


class IDPMixin(Action):
    """
    Provides a mixin for an external Identity Provider
    """

    admin_username = "admin"
    admin_password = "admin"

    admin_token_path = "/zitadel/bootstrap/admin.pat"
    organization_id_path = "/zitadel/bootstrap/org-id"

    db_host = os.getenv("DATABASE_HOST", "")
    db_port = os.getenv("DATABASE_PORT")
    db_database = os.getenv("DATABASE_NAME")
    db_user = os.getenv("DATABASE_USER")
    db_password = os.getenv("DATABASE_PASSWORD")

    external_host = os.getenv("IDP_EXTERNAL_HOST", "localhost:8800")

    idp_route = os.getenv("IDP_URL_INTERNAL", "http://zitadel-api:8080")
    idp_realm = os.getenv("IDP_OS_REALM", "openslides")

    idp_admin_route = f"{idp_route}/v2/"
    idp_scim_route = f"{idp_route}/scim/v2/"

    _idp_admin_access_token = ""
    _idp_organisation_id = ""

    def _get_admin_key(self) -> str:
        if self._idp_admin_access_token != "":
            return self._idp_admin_access_token

        # Fetch key from admin file
        try:
            with open(self.admin_token_path) as file:
                self._idp_admin_access_token = file.read().replace("\n", "")
                return self._idp_admin_access_token
        except Exception as e:
            raise ActionException(f"Error reading admin pat file: {e}") from e

    def _get_organisation_id(self) -> str:
        if self._idp_organisation_id != "":
            return self._idp_organisation_id

        # Fetch key from organization file
        try:
            with open(self.organization_id_path) as file:
                self._idp_organisation_id = file.read().replace("\n", "")
                return self._idp_organisation_id
        except Exception as e:
            raise ActionException(f"Error reading organization id file: {e}") from e

    def find_and_remove_similar_idp_users(self, user: dict) -> None:
        ## Finds IDP users that share the same identifying keys in IDP and deletes them
        idp_admin_access_token = self._get_admin_key()

        try:
            idp_org_id = self._get_organisation_id()
            response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(user["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )

            if response.status_code != 200:
                raise self.idp_error(response)

            json_response = response.json()

            if (
                "totalResult" not in json_response
                or int(json_response["totalResult"]) <= 0
            ):
                # User does not exist
                return

            found_users = json_response["Resources"]

            for u in found_users:
                self.delete_user(u)

        except Exception as e:
            raise ActionException(f"Error finding user: {e}") from e

    def create_user(self, user: dict, password: str = "") -> None:
        idp_admin_access_token = self._get_admin_key()

        os_id = user.get("id")
        username = user.get("username")
        email = user.get("email") or f"{username}@openslides.local"
        givenname = user.get("first_name") or username
        familyname = user.get("last_name") or username
        idp_org_id = self._get_organisation_id()

        # Check if there is already a IDP User with the identifying keys and delete those accounts
        self.find_and_remove_similar_idp_users(user)

        try:
            ## Upload OS user to IDP
            response = requests.post(
                f"{self.idp_scim_route}{idp_org_id}Users",
                json={
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "externalId": str(os_id),
                    **({"password": password} if password else {}),
                    "username": username,
                    "name": {
                        "givenName": givenname,
                        "familyName": familyname,
                    },
                    "emails": [
                        {
                            "value": email,
                        }
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            if response.status_code >= 400:
                raise ActionException(
                    f"Error creating User in IDP: {response.json()['detail']}"
                )
        except Exception as e:
            raise ActionException(f"Error creating user: {e}") from e

    def create_user_bulk(self, users: list[dict[str, Any]]) -> None:
        idp_admin_access_token = self._get_admin_key()
        idp_org_id = self._get_organisation_id()

        operations = []
        for ndx, user in enumerate(users):
            self.find_and_remove_similar_idp_users(user)
            external_id = user.get("id")
            username = user.get("username")
            email = user.get("email") or f"{username}@openslides.local"
            givenname = user.get("first_name") or username
            familyname = user.get("last_name") or username
            password = user.get("default_password")
            item = {
                "method": "POST",
                "path": "/Users",
                "bulkId": f"user-{ndx}",
                "data": {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "externalId": str(external_id),
                    **({"password": password} if password else {}),
                    "username": username,
                    "name": {
                        "givenName": givenname,
                        "familyName": familyname,
                    },
                    "emails": [
                        {
                            "value": email,
                        }
                    ],
                },
            }
            operations.append(item)

        operation_bulks = self.chunk_operations(operations)
        for bulk in operation_bulks:
            try:
                ## Upload OS user to IDP
                response = requests.post(
                    f"{self.idp_scim_route}{idp_org_id}/Bulk",
                    json={
                        "schemas": [
                            "urn:ietf:params:scim:api:messages:2.0:BulkRequest"
                        ],
                        "failOnErrors": 1,
                        **({"Operations": bulk}),
                    },
                    headers={
                        "Authorization": f"Bearer {idp_admin_access_token}",
                        "Host": f"{self.external_host}",
                    },
                    timeout=30,
                )
                if response.status_code >= 400:
                    raise ActionException(
                        f"Error creating User in IDP: {response.json()['detail']}"
                    )
            except Exception as e:
                raise ActionException(f"Error creating user: {e}") from e

    def chunk_operations(
        self, operations: list[dict[str, Any]]
    ) -> list[list[dict[str, Any]]]:
        return [operations[i : i + 100] for i in range(0, len(operations), 100)]

    # Deletes the OIDC user belonging to the given os user.
    def delete_user(self, instance: dict[str, Any]) -> None:
        idp_admin_access_token = self._get_admin_key()
        idp_org_id = self._get_organisation_id()

        try:
            # Request the users id from idp to have the correct id to build the SCIM delete url
            filter_response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            idp_id = self.get_idp_id(filter_response)

            ## Delete OS user from IDP
            response = requests.delete(
                self.idp_scim_route + idp_org_id + "/Users/" + idp_id,
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )

            if response.status_code != 204:
                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error deleting user: {e}") from e

            # Logs user out and thereby revokes any active session of user

    def revoke_all_sessions_of_user(self, instance: dict[str, Any]) -> None:
        idp_admin_access_token = self._get_admin_key()
        self.logger.warning(f"Revoke sessions for {instance["id"]}")
        try:
            response = requests.post(
                f"{self.idp_admin_route}sessions/search",
                json={
                    "query": {"offset": 0, "limit": 100, "asc": True},
                    "queries": [
                        {"userIdQuery": {"id": f"{instance["id"]}"}},
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            if response.status_code != 200:
                self.idp_error(response)

            json_response = response.json()

            if not "sessions" in json_response:
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
                    timeout=3,
                )

                if response.status_code != 200:
                    self.idp_error(response)

        except Exception as e:
            raise ActionException(f"Error logout of user: {e}") from e

    # Enables or disables login access in IDP for the user
    def set_user_enable_status(self, instance: dict, enabled: bool) -> None:
        idp_org_id = self._get_organisation_id()
        idp_admin_access_token = self._get_admin_key()

        try:
            filter_response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            idp_id = self.get_idp_id(filter_response)

            ## Change enable status of IDP user
            response = requests.patch(
                f"{self.idp_scim_route}{idp_org_id}/Users/{idp_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {"op": "replace", "path": "active", "value": f"{enabled}"}
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            if response.status_code != 204:
                if response.status_code == 400 and response.json()["code"] == 9:
                    self.logger.warning(
                        "User was supposed to be activated/deactivated, but was already active/inactive in IDP"
                    )
                    return

                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error setting enable status of user: {e}") from e

    # Resets users password. User has to create new password.
    # An email will be send with necessary information
    # User will be logged out
    def force_reset_password(self, instance: dict) -> None:
        idp_org_id = self._get_organisation_id()
        idp_admin_access_token = self._get_admin_key()

        filter_response = requests.get(
            f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
            headers={
                "Authorization": f"Bearer {idp_admin_access_token}",
                "Host": f"{self.external_host}",
            },
            timeout=3,
        )
        idp_id = self.get_idp_id(filter_response)

        try:
            response = requests.post(
                f"{self.idp_admin_route}users/{idp_id}/password_reset",
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )

            if response.status_code != 200:
                raise ActionException(f"{response.status_code}, {response.json()}")

        except Exception as e:
            raise ActionException(
                f"Error sending password reset email to user {idp_id}: {e}"
            ) from e

    # Updates email of user
    def update_email(self, instance: dict, email: str) -> None:
        idp_org_id = self._get_organisation_id()
        idp_admin_access_token = self._get_admin_key()

        try:
            filter_response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            idp_id = self.get_idp_id(filter_response)

            ## Change enable status of IDP user
            response = requests.patch(
                f"{self.idp_scim_route}{idp_org_id}/Users/{idp_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "replace",
                            "path": "emails[primary eq true].value",
                            "value": email,
                        }
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            if response.status_code != 204:
                if response.status_code == 400 and response.json()["code"] == 9:
                    self.logger.warning("Error updating the email of the user.")
                    return

                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error updating email of user: {e}") from e

    # Updates username of user
    def update_username(self, instance: dict, username: str) -> None:
        idp_org_id = self._get_organisation_id()
        idp_admin_access_token = self._get_admin_key()

        try:
            filter_response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            idp_id = self.get_idp_id(filter_response)

            ## Change enable status of IDP user
            response = requests.patch(
                f"{self.idp_scim_route}{idp_org_id}/Users/{idp_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "replace",
                            "path": "username",
                            "value": username,
                        }
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            if response.status_code != 204:
                if response.status_code == 400 and response.json()["code"] == 9:
                    self.logger.warning("Error updating the username of the user.")
                    return

                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error updating username of user: {e}") from e

    def update_password(self, instance: dict[str, Any], password: str) -> None:
        idp_org_id = self._get_organisation_id()
        idp_admin_access_token = self._get_admin_key()

        try:
            filter_response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            idp_id = self.get_idp_id(filter_response)

            ## Change enable status of IDP user
            response = requests.patch(
                f"{self.idp_scim_route}{idp_org_id}/Users/{idp_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "replace",
                            "path": "password",
                            "value": password,
                        }
                    ],
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            if response.status_code != 204:
                if response.status_code == 400 and response.json()["code"] == 9:
                    self.logger.warning("Error updating the username of the user.")
                    return

                self.idp_error(response)
        except Exception as e:
            raise ActionException(f"Error updating password: {e}") from e

    def user_changes_password(
        self, instance: dict[str, Any], new_password: str, old_password: str
    ) -> None:
        idp_org_id = self._get_organisation_id()
        idp_admin_access_token = self._get_admin_key()

        try:
            filter_response = requests.get(
                f'{self.idp_scim_route}{idp_org_id}/Users?filter=externalId eq "{str(instance["id"])}"',
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )
            idp_id = self.get_idp_id(filter_response)

            ## Change password of IDP user
            response = requests.patch(
                f"{self.idp_admin_route}users/{idp_id}",
                json={
                    "human": {
                        "password": {
                            "password": {"password": f"{new_password}"},
                            "currentPassword": f"{old_password}",
                        }
                    }
                },
                headers={
                    "Authorization": f"Bearer {idp_admin_access_token}",
                    "Host": f"{self.external_host}",
                },
                timeout=3,
            )

            # Logout user
            #            self.revoke_all_sessions_of_user(idp_id)

            if response.status_code != 200:
                error_response = response.json()["message"]
                self.logger.warning(error_response)
                if "COMMAND-3M0fs" in error_response:
                    raise ActionException("Old password is not correct")

                self.idp_error(response)
        except Exception as e:
            raise ActionException("Error changing password: {e}") from e

    def get_idp_id(self, response: requests.models.Response) -> str:
        resources = response.json().get("Resources")
        if resources is None or len(resources) == 0:
            raise ActionException("Could not get idp id from user. No user found")
        idp_id = resources[0].get("id", -1)

        if idp_id == -1:
            raise ActionException("Could not get idp id from user. User has no ID")
        return idp_id

    # Throws a generic error to the client while logging the real issue
    def idp_error(self, response: requests.models.Response) -> None:
        self.logger.error(f"{response.status_code} - {response.json()}")
        raise ActionException("An IDP error occured. Please contact your administrator")
