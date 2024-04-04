from datastore.reader.core.requests import GetManyRequest, GetManyRequestPart

from openslides_backend.services.datastore.read_adapter import ReadAdapter


def test_get_many(write_directly) -> None:
    # TODO: This probably writes the wrong data format.
    write_directly(
        [
            (
                "INSERT INTO organizationT (id, name, default_language, theme_id) VALUES %s",
                [
                    (1, "Orga 1", "en", 1)
                ]
            ),
            (
                "INSERT INTO themeT (id, name, accent_500, primary_500, warn_500, organization_id) VALUES %s",
                [
                    (1, "Theme 1", "#0000ff", "#00ff00", "#ff0000", 1),
                ]
            ),
            (
                "INSERT INTO committeeT (id, name, organization_id) VALUES %s, %s, %s",
                [
                    (1, "Committee 1", 1),
                    (2, "Committee 2", 1),
                    (3, "Committee 3", 1),
                ]
            )
        ]
    )
    # write(
    #     {
    #         "type": "create",
    #         "fqid": "organization/1",
    #         "fields": {
    #             "id": 1,
    #             "name": "Orga 1",
    #             "default_language": "en",
    #             "theme_id": 1,
    #             "theme_ids": [1],
    #             "committee_ids": [1, 2, 3],
    #         },
    #     },
    #     {
    #         "type": "create",
    #         "fqid": "theme/1",
    #         "fields": {
    #             "id": 1,
    #             "name": "Theme 1",
    #             "accent_500": "#0000ff",
    #             "primary_500": "#00ff00",
    #             "warn_500": "#ff0000",
    #             "theme_for_organization_id": 1,
    #             "organization_id": 1,
    #         },
    #     },
    #     {
    #         "type": "create",
    #         "fqid": "committee/1",
    #         "fields": {"id": 1, "name": "Committee 1", "organization_id": 1},
    #     },
    #     {
    #         "type": "create",
    #         "fqid": "committee/2",
    #         "fields": {"id": 2, "name": "Committee 2", "organization_id": 1},
    #     },
    #     {
    #         "type": "create",
    #         "fqid": "committee/3",
    #         "fields": {"id": 3, "name": "Committee 3", "organization_id": 1},
    #     },
    # )
    read_adapter = ReadAdapter()
    request = GetManyRequest([GetManyRequestPart("committee", [2, 3], ["id", "name"])])
    result = read_adapter.get_many(request)
    assert result["committee"] == {
        2: {"id": 2, "name": "Committee 2"},
        3: {"id": 3, "name": "Committee 3"},
    }
