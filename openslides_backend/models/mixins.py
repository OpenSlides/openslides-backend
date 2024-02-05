class AgendaItemModelMixin:
    AGENDA_ITEM = "common"
    INTERNAL_ITEM = "internal"
    HIDDEN_ITEM = "hidden"


class MeetingModelMixin:
    LOGO_PLACES = (
        "projector_main",
        "projector_header",
        "web_header",
        "pdf_header_l",
        "pdf_header_r",
        "pdf_footer_l",
        "pdf_footer_r",
        "pdf_ballot_paper",
    )
    FONT_PLACES = (
        "regular",
        "italic",
        "bold",
        "bold_italic",
        "monospace",
        "chyron_speaker_name",
        "projector_h1",
        "projector_h2",
    )
    DEFAULT_PROJECTOR_OPTIONS = (
        "agenda_item_list",
        "topic",
        "list_of_speakers",
        "current_list_of_speakers",
        "motion",
        "amendment",
        "motion_block",
        "assignment",
        "mediafile",
        "message",
        "countdown",
        "assignment_poll",
        "motion_poll",
        "poll",
    )

    @classmethod
    def all_logo_places(cls) -> list[str]:
        return [f"logo_{place}_id" for place in cls.LOGO_PLACES]

    @classmethod
    def reverse_logo_places(cls) -> list[str]:
        return [f"used_as_logo_{place}_in_meeting_id" for place in cls.LOGO_PLACES]

    @classmethod
    def all_font_places(cls) -> list[str]:
        return [f"font_{place}_id" for place in cls.FONT_PLACES]

    @classmethod
    def reverse_font_places(cls) -> list[str]:
        return [f"used_as_font_{place}_in_meeting_id" for place in cls.FONT_PLACES]

    @classmethod
    def all_default_projectors(cls) -> list[str]:
        return [
            f"default_projector_{option}_ids"
            for option in cls.DEFAULT_PROJECTOR_OPTIONS
        ]

    @classmethod
    def reverse_default_projectors(cls) -> list[str]:
        return [
            f"used_as_default_projector_for_{option}_in_meeting_id"
            for option in cls.DEFAULT_PROJECTOR_OPTIONS
        ]


class PollModelMixin:
    STATE_CREATED = "created"
    STATE_STARTED = "started"
    STATE_FINISHED = "finished"
    STATE_PUBLISHED = "published"

    TYPE_ANALOG = "analog"
    TYPE_NAMED = "named"
    TYPE_PSEUDOANONYMOUS = "pseudoanonymous"

    ONEHUNDRED_PERCENT_BASE_Y = "Y"
    ONEHUNDRED_PERCENT_BASE_YN = "YN"
    ONEHUNDRED_PERCENT_BASE_YNA = "YNA"
    ONEHUNDRED_PERCENT_BASE_N = "N"
    ONEHUNDRED_PERCENT_BASE_VALID = "valid"
    ONEHUNDRED_PERCENT_BASE_CAST = "cast"
    ONEHUNDRED_PERCENT_BASE_ENTITLED = "entitled"
    ONEHUNDRED_PERCENT_BASE_ENTITLED_PRESENT = "entitled_present"
    ONEHUNDRED_PERCENT_BASE_DISABLED = "disabled"
