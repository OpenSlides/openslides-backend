def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "organization/1", "fields": {"id": 42}})
    write({"type": "update", "fqid": "organization/1", "fields": {"f": 2}})
    write({"type": "delete", "fqid": "organization/1"})
    write({"type": "restore", "fqid": "organization/1"})

    finalize("0009_add_organization_mail_defaults")

    assert_model(
        "organization/1",
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
        "organization/1",
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
        "organization/1",
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
        "organization/1",
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
