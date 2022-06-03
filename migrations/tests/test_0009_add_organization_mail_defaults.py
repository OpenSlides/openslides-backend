ONE_ORGANIZATION_FQID = "organization/1"


def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {"id": 42}})
    write({"type": "update", "fqid": ONE_ORGANIZATION_FQID, "fields": {"f": 2}})
    write({"type": "delete", "fqid": ONE_ORGANIZATION_FQID})
    write({"type": "restore", "fqid": ONE_ORGANIZATION_FQID})

    finalize("0009_add_organization_mail_defaults")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "users_email_sender": "OpenSlides",
            "users_email_subject": "OpenSlides access data",
            "users_email_body": """      Dear {name},



      this is your personal OpenSlides login:

          {url}

          username: {username}

          password: {password}



      This email was generated automatically.""",
            "url": "http://example.com:8000",
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "users_email_sender": "OpenSlides",
            "users_email_subject": "OpenSlides access data",
            "users_email_body": """      Dear {name},



      this is your personal OpenSlides login:

          {url}

          username: {username}

          password: {password}



      This email was generated automatically.""",
            "url": "http://example.com:8000",
            "f": 2,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "users_email_sender": "OpenSlides",
            "users_email_subject": "OpenSlides access data",
            "users_email_body": """      Dear {name},



      this is your personal OpenSlides login:

          {url}

          username: {username}

          password: {password}



      This email was generated automatically.""",
            "url": "http://example.com:8000",
            "f": 2,
            "meta_deleted": True,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "users_email_sender": "OpenSlides",
            "users_email_subject": "OpenSlides access data",
            "users_email_body": """      Dear {name},



      this is your personal OpenSlides login:

          {url}

          username: {username}

          password: {password}



      This email was generated automatically.""",
            "url": "http://example.com:8000",
            "f": 2,
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
