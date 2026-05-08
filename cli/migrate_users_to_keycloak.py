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

db_host = get_config("DATABASE_HOST")
db_port = get_config("DATABASE_PORT")
db_database = get_config("DATABASE_NAME")
db_user = get_config("DATABASE_USER")
db_password = get_config("DATABASE_PASSWORD")

keycloak_url = get_config("KEYCLOAK_URL_INTERNAL", "http://keycloak-server:8080")
keycloak_realm = get_config("KEYCLOAK_OS_REALM", "openslides")

keycloak_admin_route = f"{keycloak_url}/admin/realms/{keycloak_realm}/"

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
def get_admin_key():
    try:
        response = requests.post(f"{keycloak_url}/realms/master/protocol/openid-connect/token",
            data={
                'client_id': "admin-cli",
                'username': admin_username,
                'password': admin_password,
                'grant_type': "password",
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        json_response = response.json()

        if response.status_code != 200:
            raise Exception(f"{response.status_code} {json_response}")

        return json_response["access_token"]
    except Exception as e:
        logger.error(f"Error receiving keycloak admin token: {e}")
    return None

# Returns keycloak id of an existing keycloak user with matching username
def get_keycloak_id_by_username(keycloak_admin_key, username):
    try:
        response = requests.get(keycloak_admin_route + "users?username=" + username,
            headers={
                'Authorization': f'Bearer {keycloak_admin_key}'
            }
        )

        json_response = response.json()

        if response.status_code != 200:
            raise Exception(f"{response.status_code} {json_response}")

        return json_response[0]['id']
    except Exception as e:
        logger.error(f"Error getting keycloak user by username: {e}")
    return None

def get_name_of_keycloak_user(keycloak_admin_key, keycloak_id):
    try:
        response = requests.get(keycloak_admin_route + "users/" + keycloak_id,
            headers={
                'Authorization': f'Bearer {keycloak_admin_key}'
            }
        )

        json_response = response.json()

        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise Exception(f"{response.status_code} {json_response}")

        return json_response['username']
    except Exception as e:
        logger.error(f"Error getting keycloak user: {e}")
    return None

# Creates a keycloak user for given OS user. Returns keycloak id of newly created user.
# Returns existing keycloak users id, if a keycloak user of given username already exists
def migrate_and_create_user(keycloak_admin_key, username):
    try:
        response = requests.post(keycloak_admin_route + "users",
            json={
                'username': username,
                'enabled': True,
            },
            headers={
                'Authorization': f'Bearer {keycloak_admin_key}',
            }
        )

        if response.status_code != 201 and response.status_code != 409:
            raise Exception(f"{response.status_code}, {response}")

        return get_keycloak_id_by_username(keycloak_admin_key, username)
    except Exception as e:
        logger.error(f"Error migrating/creating keycloak user: {e}")
    return None

# This adds '=' for argon2 padding at the end of a password or salt. It needs to pad until the length of the string is divisible by 4
def hash_padding(to_pad):
    return to_pad + '=' * (-len(to_pad) % 4)

# Exports password to keycloak user
def migrate_password(keycloak_admin_key, keycloak_id, password):
    if len(password) == 152:
        try:
            # SHA512 password
            response = requests.put(keycloak_admin_route + "users/" + keycloak_id,
                json={
                    'credentials' : [{
                        'type': 'password',
                        'credentialData': json.dumps({
                            'algorithm': 'sha512',
                            'hashIterations': 1
                        }),
                        'secretData': json.dumps({
                            'value': base64.b64encode((password[64:]).encode('utf-8')).decode('utf-8'),
                            'salt': base64.b64encode((password[:64]).encode('utf-8')).decode('utf-8')
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
    else:
        try:
            # argon2 password
            response = requests.put(keycloak_admin_route + "users/" + keycloak_id,
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
                    'Authorization': f'Bearer {keycloak_admin_key}',
                }
            )

            if response.status_code != 204:
                raise Exception(f"{response.status_code} {response.json()}")
        except Exception as e:
            logger.error(f"Error migrating password for keycloak user {keycloak_id}: {e}")

# Exports email to keycloak user
def migrate_email(keycloak_admin_key, keycloak_id, email):
    try:
        response = requests.put(keycloak_admin_route + "users/" + keycloak_id,
            json={
                'email': email,
            },
            headers={
                'Authorization': f'Bearer {keycloak_admin_key}',
            }
        )

        if response.status_code != 204:
            raise Exception(f"{response.status_code} {response.json()}")
    except Exception as e:
        logger.error(f"Error migrating password for keycloak user {keycloak_id}: {e}")
    return

def main() -> None:
    conn = create_connection()

    ## Get Admin Key
    keycloak_admin_key = get_admin_key()

    user_keycloak_map = {}

    ## Iterate all OS Users
    with conn.cursor() as cursor:

        cursor.execute("SELECT username, password, email, keycloak_id FROM user_t;")

        for user in cursor:
            username = user[0]
            password = user[1]
            email = user[2]
            existing_keycloak_id = user[3]

            if email == None:
                email = f"{username}@missing-email.com"

            if existing_keycloak_id is None or existing_keycloak_id == "":
                # No Keycloak ID set. This OS User likely has no Keycloak Account yet

                ## Upload OS user to Keycloak
                keycloak_user_id = migrate_and_create_user(keycloak_admin_key, username)

                if keycloak_user_id == None:
                    raise Exception(f"Error migrating or finding user {username}")
            else:
                # A Keycloak ID already exists. Check if it points to the correct OS User
                keycloak_username = get_name_of_keycloak_user(keycloak_admin_key, existing_keycloak_id)

                if keycloak_username is None:
                    # No user with that id exists at all, create new one
                    keycloak_user_id = migrate_and_create_user(keycloak_admin_key, username)

                    if keycloak_user_id == None:
                        raise Exception(f"Error migrating or finding user {username}")
                elif keycloak_username != username:
                    # Keycloak User exists, but is different from OS User
                    raise Exception(f"Error: {username} already has a keycloak id in the database. However, that Keycloak ID points to {keycloak_username}")
                else:
                    # Keycloak User exists and is the same as OS User
                    keycloak_user_id = existing_keycloak_id

            ## Migrate Data
            migrate_email(keycloak_admin_key, keycloak_user_id, email)

            migrate_password(keycloak_admin_key, keycloak_user_id, password)

            ## Link username with keycloak id for later use
            user_keycloak_map[username] = keycloak_user_id

    ## Record Keycloak ID to OS User
    for username, keycloak_user_id in user_keycloak_map.items():
        with conn.cursor() as cursor:
            cursor.execute(f"UPDATE user_t SET keycloak_id = '{keycloak_user_id}' WHERE username = '{username}';")

    ## Commit user changes
    conn.commit()

if __name__ == "__main__":
    main()
