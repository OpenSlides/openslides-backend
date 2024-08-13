from ...services.datastore.interface import DatastoreService, PartialModel
from ...shared.filters import And, Filter, FilterOperator


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
