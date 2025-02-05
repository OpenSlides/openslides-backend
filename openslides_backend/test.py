from keycloak import KeycloakAdmin

# main
if __name__ == "__main__":
    KeycloakAdmin(server_url="http://keycloak:8080/idp/",
                  username="admin",
                  password="admin",
                  realm_name="master",
                  verify=False).get_users()