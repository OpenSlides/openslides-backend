from datastore.reader.core.requests import GetManyRequest, GetManyRequestPart

from openslides_backend.services.datastore.read_adapter import ReadAdapter


def test_get_many(write_directly) -> None:
    # TODO: This probably writes the wrong data format.
    cleanup = write_directly(
        [
            {
                "table": "organizationT",
                "fields": ["id", "name", "default_language", "theme_id"],
                "rows": [(1, "Orga 1", "en", 1)]
            },
            {
                "table": "themeT",
                "fields": ["id", "name", "accent_500", "primary_500", "warn_500"],
                "rows": [(1, "Theme 1", 255, 256*255, 256*256*255)]
            },
            {
                "table": "committeeT",
                "fields": ["id", "name"],
                "rows": [
                    (1, "Committee 1"),
                    (2, "Committee 2"),
                    (3, "Committee 3"),
                ]
            }
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
    cleanup()
