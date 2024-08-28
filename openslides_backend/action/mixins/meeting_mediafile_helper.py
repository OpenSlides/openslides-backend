from typing import Any

from ...services.datastore.interface import DatastoreService, PartialModel
from ...shared.exceptions import ActionException
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


def get_meeting_mediafile_id_or_create_payload(
    datastore: DatastoreService,
    meeting_id: int,
    mediafile_id: int,
) -> int | dict[str, Any]:
    id_, m_mediafile = find_meeting_mediafile_generate_implicit(
        datastore,
        meeting_id,
        mediafile_id,
        ["meeting_id", "mediafile_id", "inherited_access_group_ids", "is_public"],
    )
    if id_:
        return id_
    mediafile = datastore.get(
        fqid_from_collection_and_id("mediafile", mediafile_id),
        ["parent_id", "published_to_meetings_in_organization_id"],
    )
    if not mediafile.get("published_to_meetings_in_organization_id"):
        raise ActionException(
            "No meeting_mediafile creation possible: Mediafile is not published."
        )
    if not mediafile.get("parent_id"):
        m_mediafile["access_group_ids"] = m_mediafile["inherited_access_group_ids"]
    return m_mediafile


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
