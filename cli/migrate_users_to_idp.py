import psycopg
import logging
import os
import requests
import json
import base64

logger = logging.getLogger(__name__)

def get_config(key, default=""):
    return os.getenv(key, default)

admin_username="admin"
admin_password="admin"

admin_token_path = "/zitadel/bootstrap/admin.pat"

db_host = get_config("DATABASE_HOST")
db_port = get_config("DATABASE_PORT")
db_database = get_config("DATABASE_NAME")
db_user = get_config("DATABASE_USER")
db_password = get_config("DATABASE_PASSWORD")

external_route = get_config("IDP_URL_EXTERNAL", "localhost:8080")

idp_route = get_config("IDP_URL_INTERNAL", "http://zitadel-api:8080")
idp_realm = get_config("IDP_OS_REALM", "openslides")

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
        logger.error(f"Error during connect to the database: " f"{repr(e)}")
        pass

# Returns access token of the REST API admin
def get_admin_key() -> str:
    # Fetch key from admin file
    try:
        with open(admin_token_path) as file:
            idp_admin_access_token = file.read().replace("\n","")
            return idp_admin_access_token
    except Exception as e:
        logger.error(f"Error reading admin pat file: {e}")
    return ""

# Returns idp id of an existing idp user with matching username
def get_idp_id_by_username(idp_admin_key, username):
    try:
        response = requests.get(idp_admin_route + "users?username=" + username,
            headers={
                'Authorization': f'Bearer {idp_admin_key}'
            }
        )

        json_response = response.json()

        if response.status_code != 200:
            raise Exception(f"{response.status_code} {json_response}")

        return json_response[0]['id']
    except Exception as e:
        logger.error(f"Error getting idp user by username: {e}")
    return None

def get_name_of_idp_user(idp_admin_key, idp_id):
    try:
        response = requests.get(idp_admin_route + "users/" + idp_id,
            headers={
                'Authorization': f'Bearer {idp_admin_key}'
            }
        )

        json_response = response.json()

        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise Exception(f"{response.status_code} {json_response}")

        return json_response['username']
    except Exception as e:
        logger.error(f"Error getting idp user: {e}")
    return None

# Creates an IDP user for given OS user. Returns idp id of newly created user.
# Returns existing idp users id, if a idp user of given username already exists
def migrate_and_create_user(idp_admin_access_token, username, os_id, email, password):
    try:
        response = requests.post(
        f"{idp_admin_route}organizations/_search",
            headers={
                'Authorization': f'Bearer {idp_admin_access_token}',
                'Content-Type': 'application/json',
                'Host': 'localhost:8080'
            },
            json={},
            timeout=20,
        )

        organisationId = response.json()["result"][0]["id"]

        ## Upload OS user to IDP
        response = requests.post(idp_admin_route + "users/new",
            json={
                'username': username,
                'organizationId': organisationId,
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
                'Host': f'{external_route}'
            }
        )

        if response.status_code == 200:
            return response.json()["id"]
        elif response.status_code == 409:
            logger.error(f"A user named {username} already exists in IDP.")
        else:
            logger.error(f"Response: {response.status_code} {response.json()}")
    except Exception as e:
        logger.error(f"Error creating user: {e}")

    return ""

# This adds '=' for argon2 padding at the end of a password or salt. It needs to pad until the length of the string is divisible by 4
def hash_padding(to_pad):
    return to_pad + '=' * (-len(to_pad) % 4)

# Exports password to idp user
def migrate_password(idp_admin_key, idp_id, password):
    if len(password) == 152:
        # This password is likely SHA512 encoded. The user must therefore reset their password
        logger.warning(f"{idp_id} has a deprecated SHA512-encrypted password. They must reset their password on next visit")
        try:
            response = requests.put(idp_admin_route + "users/" + idp_id + "/execute-actions-email",
                json=[
                        'UPDATE_PASSWORD'
                    ]
                ,
                headers={
                    'Authorization': f'Bearer {idp_admin_key}',
                }
            )

            if response.status_code != 204:
                raise Exception(f"{response.status_code}, {response.json()}")
        except Exception as e:
            logger.error(f"Error sending password reset email to user: {e}")
    else:
        try:
            # argon2 password
            response = requests.put(idp_admin_route + "users/" + idp_id,
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
                            'value': hash_padding(password.split('$')[5]),
                            'salt': hash_padding(password.split('$')[4]),
                        }),
                    }]
                },
                headers={
                    'Authorization': f'Bearer {idp_admin_key}',
                }
            )

            if response.status_code != 204:
                raise Exception(f"{response.status_code} {response.json()}")
        except Exception as e:
            logger.error(f"Error migrating password for idp user {idp_id}: {e}")

# Exports email to idp user
def migrate_email(idp_admin_key, idp_id, email):
    try:
        response = requests.put(idp_admin_route + "users/" + idp_id,
            json={
                'email': email,
            },
            headers={
                'Authorization': f'Bearer {idp_admin_key}',
            }
        )

        if response.status_code != 204:
            raise Exception(f"{response.status_code} {response.json()}")
    except Exception as e:
        logger.error(f"Error migrating password for idp user {idp_id}: {e}")
    return

def user_stress_test(users_to_add) -> None:
    for i in range(users_to_add):
        username = "user-" + str(i)
        password = "fsafasf"
        email = "user-" + str(i) + "@email.com"
        existing_idp_id = ""
        os_id = i

        idp_user_id = migrate_and_create_user(idp_admin_key, username, os_id, email, password)

        if idp_user_id == None:
            raise Exception(f"Error migrating or finding user {username}")

def main() -> None:
    conn = create_connection()

    ## Get Admin Key
    idp_admin_access_token = get_admin_key()

    user_idp_map = {}
    ## Iterate all OS Users
    with conn.cursor() as cursor:

        cursor.execute("SELECT username, password, email, idp_id, id FROM user_t;")

        for user in cursor:
            username = user[0]
            password = user[1]
            email = user[2]
            existing_idp_id = user[3]
            os_id = user[4]

            if email == None:
                email = f"{username}@missing-email.com"

            if existing_idp_id is None or existing_idp_id == "":
                # No IDP ID set. This OS User likely has no IDP Account yet
                logger.warning(f"Create new user {username}")

                ## Upload OS user to IDP
                idp_user_id = migrate_and_create_user(idp_admin_access_token, username, os_id, email, password)

                logger.warning(f"ID: {idp_user_id}")
                if idp_user_id == None:
                    raise Exception(f"Error migrating or finding user {username}. No ID")
            else:
                logger.warning(f"Update existing user {username} with id {existing_idp_id}")
                # A IDP ID already exists. Check if it points to the correct OS User
                idp_username = get_name_of_idp_user(idp_admin_access_token, existing_idp_id)

                if idp_username is None:
                    # No user with that id exists at all, create new one
                    idp_user_id = migrate_and_create_user(idp_admin_access_token, username, os_id, email)

                    if idp_user_id == None:
                        raise Exception(f"Error migrating or finding user {username}")
                elif idp_username != username:
                    # IDP User exists, but is different from OS User
                    raise Exception(f"Error: {username} already has a idp id in the database. However, that IDP ID points to {idp_username}")
                else:
                    # IDP User exists and is the same as OS User
                    idp_user_id = existing_idp_id

            ## Link username with idp id for later use
            user_idp_map[username] = idp_user_id

    ## Record IDP ID to OS User
    for username, idp_user_id in user_idp_map.items():
        with conn.cursor() as cursor:
            cursor.execute("UPDATE user_t SET idp_id = %s WHERE username = %s", (idp_user_id, username))

    ## Commit user changes
    conn.commit()

if __name__ == "__main__":
    main()
