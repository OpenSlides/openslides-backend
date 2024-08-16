from ...services.datastore.interface import DatastoreService, PartialModel
from ...shared.filters import And, Filter, FilterOperator
from ...shared.patterns import fqid_from_collection_and_id


def get_meeting_mediafile_filter(meeting_id: int, mediafile_id: int) -> Filter:
    return And(
        FilterOperator("meeting_id", "=", meeting_id),
        FilterOperator("mediafile_id", "=", mediafile_id),
    )


def find_meeting_mediafile(
    datastore: DatastoreService,
    meeting_id: int,
    mediafile_id: int,
    mapped_fields: list[str] = [],
) -> tuple[int | None, PartialModel]:
    m_mediafiles = datastore.filter(
        "meeting_mediafile",
        get_meeting_mediafile_filter(meeting_id, mediafile_id),
        list({"id", *mapped_fields}),
    )
    assert len(m_mediafiles) <= 1
    if len(m_mediafiles):
        id_ = list(m_mediafiles)[0]
        return (id_, m_mediafiles[id_])
    return (None, {})


def find_meeting_mediafile_generate_implicit(
    datastore: DatastoreService,
    meeting_id: int,
    mediafile_id: int,
    mapped_fields: list[str] = [],
) -> tuple[int | None, PartialModel]:
    result = find_meeting_mediafile(datastore, meeting_id, mediafile_id, mapped_fields)
    if result[0]:
        return result
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id), ["admin_group_id"]
    )
    fake_meeting_mediafile = {
        "meeting_id": meeting_id,
        "mediafile_id": mediafile_id,
        "inherited_access_group_ids": [meeting["admin_group_id"]],
        "is_public": False,
    }
    return (
        None,
        {
            field: fake_meeting_mediafile.get(field)
            for field in mapped_fields
            if field in fake_meeting_mediafile
        },
    )
