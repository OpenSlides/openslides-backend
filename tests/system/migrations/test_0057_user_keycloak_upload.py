def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {
                "id": 1,
                "username": "adam_sandler",
            },
        },
    )
    write(
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {
                "id": 2,
                "username": "stifflers",
                "saml_id": "mom"
            },
        },
    )

    finalize("0057_user_keycloak_upload")

    assert_model(
        "user/1",
        {
            "id": 1,
            "username": "adam_sandler",
            "idp_id": "adam_sandler"
        },
    )
    assert_model(
        "user/2",
        {
            "id": 2,
            "username": "stifflers",
             "idp_id": "stifflers_mom"
        },
    )