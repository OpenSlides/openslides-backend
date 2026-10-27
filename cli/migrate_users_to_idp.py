import base64
import logging
import os

import psycopg
import requests

logger = logging.getLogger(__name__)


def get_config(key, default=""):
    return os.getenv(key, default)


admin_token_path = "/zitadel/bootstrap/admin.pat"
organization_id_path = "/zitadel/bootstrap/org-id"

db_host = get_config("DATABASE_HOST")
db_port = get_config("DATABASE_PORT")
db_database = get_config("DATABASE_NAME")
db_user = get_config("DATABASE_USER")
db_password = get_config("DATABASE_PASSWORD")

external_host = get_config("IDP_EXTERNAL_HOST", "localhost:8800")

idp_route = get_config("IDP_URL_INTERNAL", "http://zitadel-api:8080")

idp_admin_route = f"{idp_route}/v2/"


def create_connection():
    try:
        return psycopg.connect(
            host=db_host,
            port=db_port,
            dbname=db_database,
            user=db_user,
            password=db_password,
        )
    except psycopg.Error as e:
        raise Exception(f"Error during connect to the database: {e}")


def create_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Host": external_host,
        }
    )
    return session


# Returns access token of the REST API admin
def get_admin_key() -> str:
    # Fetch key from admin file
    try:
        with open(admin_token_path) as file:
            idp_admin_access_token = file.read().replace("\n", "")
            return idp_admin_access_token
    except Exception as e:
        raise Exception(f"Error reading admin pat file: {e}")


def get_organization_id() -> str:
    # Fetch key from organization file
    try:
        with open(organization_id_path) as file:
            idp_organization_id = file.read().replace("\n", "")
            return idp_organization_id
    except Exception as e:
        raise Exception(f"Error reading organization id file: {e}")


# Returns IDP user data
def get_name_of_idp_user(session, idp_id) -> str:
    try:
        response = session.get(idp_admin_route + "users/" + idp_id)

        if response.status_code == 404:
            return ""
        elif response.status_code != 200:
            raise Exception(f"{response.status_code} {response.json()}")

        json_response = response.json()

        return json_response["user"]["username"]
    except Exception as e:
        raise Exception(f"Error getting idp user: {e}")


# Creates an IDP user for given OS user. Returns idp id of newly created user.
# Throws error, if an idp user of given username already exists
def migrate_and_create_user(
    requestSession, organization_id, username, os_id, email, password
) -> str:
    idp_id = ""
    human = {
        "profile": {"givenName": username, "familyName": username},
        "email": {"email": email, "isVerified": True},
    }
    # Skip if password is empty
    if password:
        human["hashedPassword"] = {"hash": password}
    try:
        # Upload OS user to IDP
        response = requestSession.post(
            idp_admin_route + "users/new",
            json={
                "username": username,
                "organizationId": organization_id,
                "human": human,
                "metadata": [
                    {
                        "key": "os_id",
                        "value": base64.b64encode(str(os_id).encode("utf-8")).decode(
                            "ascii"
                        ),
                    },
                ],
            },
        )

        if response.status_code == 200:
            idp_id = response.json()["id"]
        elif response.status_code == 409:
            raise Exception(f"A user named {username} already exists in IDP.")
        else:
            raise Exception(
                f"ID returned by IDP is empty. Unexpected response: {response.text}"
            )
    except Exception as e:
        raise Exception(f"Error creating user: {e}")

    return idp_id


def user_stress_test(users_to_add) -> None:
    # Get Admin Key
    idp_admin_access_token = get_admin_key()
    organization_id = get_organization_id()

    session = create_session(idp_admin_access_token)

    for i in range(users_to_add):
        username = "user-" + str(i)
        password = "$argon2id$v=19$m=65536,t=3,p=4$OXRxaWhTU2JnNkFvdnBDRg$Hqd6Us8drdCsBo3gpYth0Q"
        email = "user-" + str(i) + "@email.com"
        os_id = i

        migrate_and_create_user(
            session, organization_id, username, os_id, email, password
        )


def main() -> None:
    with create_connection() as conn:
        # Get Admin Key
        idp_admin_access_token = get_admin_key()
        organization_id = get_organization_id()

        session = create_session(idp_admin_access_token)

        user_idp_map = {}
        # Iterate all OS Users
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, password, email, idp_id, id FROM user_t;")

            for user in cursor:
                username = user[0]
                password = user[1]
                email = user[2]
                existing_idp_id = user[3]
                os_id = user[4]

                if not email:
                    email = f"{username}@openslides.local"

                if not existing_idp_id:
                    # No IDP ID set. This OS User likely has no IDP Account yet
                    logger.warning(f"Create new user {username}")

                    # Upload OS user to IDP
                    idp_user_id = migrate_and_create_user(
                        session, organization_id, username, os_id, email, password
                    )
                else:
                    logger.warning(
                        f"User {username} already exists with id {existing_idp_id}"
                    )
                    # An IDP ID already exists. Check if it points to the correct OS User
                    idp_username = get_name_of_idp_user(session, existing_idp_id)

                    if idp_username == "":
                        # No user with that id exists at all, create new one
                        idp_user_id = migrate_and_create_user(
                            session, organization_id, username, os_id, email, password
                        )
                    elif idp_username != username:
                        # IDP User exists, but is different from OS User
                        raise Exception(
                            f"Error: {username} already has an idp id in the database. However, that IDP ID points to {idp_username}"
                        )
                    else:
                        # IDP User exists and is the same as OS User
                        idp_user_id = existing_idp_id

                # Link username with idp id for later use
                user_idp_map[username] = idp_user_id

        # Record IDP ID to OS User
        with conn.cursor() as cursor:
            cursor.executemany(
                "UPDATE user_t SET idp_id = %s WHERE username = %s",
                [(idp_id, username) for username, idp_id in user_idp_map.items()],
            )

        # Commit user changes
        conn.commit()


if __name__ == "__main__":
    main()
