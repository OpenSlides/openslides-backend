from ...shared.filters import And, Filter, FilterOperator


def get_meeting_mediafile_filter(meeting_id: int, mediafile_id: int) -> Filter:
    return And(
        FilterOperator("meeting_id", "=", meeting_id),
        FilterOperator("mediafile_id", "=", mediafile_id),
    )
