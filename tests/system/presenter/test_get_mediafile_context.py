from typing import Any, Literal

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID

from .base import BasePresenterTestCase


class TestGetUserRelatedModels(BasePresenterTestCase):
    def test_get_mediafile_context_simple(self) -> None:
        self.set_models({"mediafile/1": {"owner_id": ONE_ORGANIZATION_FQID}})
        status_code, data = self.request(
            "get_mediafile_context", {"mediafile_ids": [1]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": False,
                "children_amount": 0,
                "meetings_of_interest": {},
            }
        }

    def test_get_mediafile_context_meeting_simple(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "...",
                    "mediafile_ids": [1],
                    "meeting_mediafile_ids": [1],
                },
                "mediafile/1": {"owner_id": "meeting/1", "meeting_mediafile_ids": [1]},
                "meeting_mediafile/1": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                },
            }
        )
        status_code, data = self.request(
            "get_mediafile_context", {"mediafile_ids": [1]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "owner_id": "meeting/1",
                "published": False,
                "children_amount": 0,
                "meetings_of_interest": {},
            }
        }

    def test_get_mediafile_context_multiple_complex(self) -> None:
        def get_topic(
            id_: int, meeting_id: int, attachment_ids: list[int]
        ) -> dict[str, dict[str, Any]]:
            return {
                f"topic/{id_}": {
                    "meeting_id": meeting_id,
                    "attachment_ids": attachment_ids,
                },
            }

        def get_projection(
            meeting_id: int,
            mmediafile_id: int,
            projector_id: int,
            proj_type: Literal["current", "history", "preview"],
        ) -> dict[str, Any]:
            return {
                "meeting_id": meeting_id,
                "content_object_id": f"meeting_mediafile/{mmediafile_id}",
                f"{proj_type}_projector_id": projector_id,
            }

        def get_m_mediafile(
            meeting_id: int, mediafile_id: int, additional_data: dict[str, Any] = {}
        ) -> dict[str, Any]:
            return {
                "meeting_id": meeting_id,
                "mediafile_id": mediafile_id,
                "is_public": False,
                "inherited_access_group_ids": [meeting_id],
                **additional_data,
            }

        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "mediafile_ids": [4, 5, 6, 7, 8, 9],
                    "published_mediafile_ids": [4, 5, 6, 7, 8, 9],
                },
                "meeting/1": {
                    "name": "Meeting 1",
                    "mediafile_ids": [1],
                    "meeting_mediafile_ids": [1, 4, 6],
                    "topic_ids": [1, 4],
                    "projector_ids": [1, 4],
                    "all_projection_ids": [1, 2, 8],
                    "logo_projector_header_id": 1,
                    "font_bold_italic_id": 1,
                    "group_ids": [1],
                    "admin_group_id": 1,
                },
                "group/1": {
                    "name": "Group 1",
                    "meeting_id": 1,
                    "admin_group_for_meeting_id": 1,
                    "mediafile_access_group_ids": [4],
                    "mediafile_inherited_access_group_ids": [4, 6],
                },
                "projector/1": {
                    "meeting_id": 1,
                    "preview_projection_ids": [2],
                    "history_projection_ids": [1],
                },
                "projection/1": get_projection(1, 1, 1, "history"),
                "projection/2": get_projection(1, 4, 1, "preview"),
                "projector/4": {
                    "meeting_id": 1,
                    "current_projection_ids": [8],
                },
                "projection/8": get_projection(1, 1, 4, "current"),
                **get_topic(1, 1, [1]),
                **get_topic(4, 1, [1]),
                "meeting_mediafile/1": get_m_mediafile(
                    1,
                    1,
                    {
                        "access_group_ids": [],
                        "inherited_access_group_ids": [],
                        "is_public": True,
                        "projection_ids": [1, 8],
                        "attachment_ids": ["topic/1", "topic/4"],
                        "used_as_logo_projector_header_in_meeting_id": 1,
                        "used_as_font_bold_italic_in_meeting_id": 1,
                    },
                ),
                "meeting_mediafile/4": get_m_mediafile(
                    1,
                    4,
                    {
                        "access_group_ids": [1],
                        "projection_ids": [2],
                    },
                ),
                "meeting_mediafile/6": get_m_mediafile(1, 5),
                "meeting/2": {
                    "name": "Meeting 2",
                    "mediafile_ids": [2, 3],
                    "meeting_mediafile_ids": [2, 3, 5, 7, 10, 12, 14],
                    "topic_ids": [2],
                    "projector_ids": [2],
                    "all_projection_ids": [3, 4, 5, 6],
                    "logo_web_header_id": 7,
                    "font_monospace_id": 10,
                    "group_ids": [2],
                    "admin_group_id": 2,
                },
                "group/2": {
                    "name": "Group 2",
                    "meeting_id": 2,
                    "admin_group_for_meeting_id": 2,
                    "mediafile_access_group_ids": [2, 5, 14],
                    "mediafile_inherited_access_group_ids": [2, 3, 5, 7, 10, 12, 14],
                },
                "projector/2": {
                    "meeting_id": 2,
                    "current_projection_ids": [5],
                    "preview_projection_ids": [4],
                    "history_projection_ids": [3, 6],
                },
                "projection/3": get_projection(2, 2, 2, "history"),
                "projection/4": get_projection(2, 3, 2, "preview"),
                "projection/5": get_projection(2, 7, 2, "current"),
                "projection/6": get_projection(2, 12, 2, "history"),
                **get_topic(2, 2, [3]),
                "meeting_mediafile/2": get_m_mediafile(
                    2,
                    2,
                    {
                        "access_group_ids": [2],
                        "projection_ids": [3],
                    },
                ),
                "meeting_mediafile/3": get_m_mediafile(
                    2, 3, {"projection_ids": [4], "attachment_ids": ["topic/2"]}
                ),
                "meeting_mediafile/5": get_m_mediafile(
                    2,
                    4,
                    {
                        "access_group_ids": [2],
                    },
                ),
                "meeting_mediafile/7": get_m_mediafile(
                    2,
                    5,
                    {"projection_ids": [5], "used_as_logo_web_header_in_meeting_id": 2},
                ),
                "meeting_mediafile/10": get_m_mediafile(
                    2, 7, {"used_as_font_monospace_in_meeting_id": 2}
                ),
                "meeting_mediafile/12": get_m_mediafile(
                    2,
                    8,
                    {
                        "projection_ids": [6],
                    },
                ),
                "meeting_mediafile/14": get_m_mediafile(
                    2,
                    9,
                    {
                        "access_group_ids": [2],
                    },
                ),
                "meeting/3": {
                    "name": "Meeting 3",
                    "mediafile_ids": [],
                    "meeting_mediafile_ids": [8, 9, 11, 13],
                    "topic_ids": [3],
                    "projector_ids": [3],
                    "all_projection_ids": [7],
                    "logo_pdf_header_r_id": 9,
                    "group_ids": [3],
                    "admin_group_id": 3,
                },
                "group/3": {
                    "name": "Group 3",
                    "meeting_id": 3,
                    "admin_group_for_meeting_id": 3,
                    "mediafile_access_group_ids": [9],
                    "mediafile_inherited_access_group_ids": [8, 9, 11, 13],
                },
                "projector/3": {
                    "meeting_id": 3,
                    "current_projection_ids": [7],
                },
                "projection/7": get_projection(3, 13, 3, "current"),
                **get_topic(3, 3, [8, 9]),
                "meeting_mediafile/8": get_m_mediafile(
                    3, 5, {"attachment_ids": ["topic/3"]}
                ),
                "meeting_mediafile/9": get_m_mediafile(
                    3,
                    6,
                    {
                        "access_group_ids": [3],
                        "attachment_ids": ["topic/3"],
                        "used_as_logo_pdf_header_r_in_meeting_id": 3,
                    },
                ),
                "meeting_mediafile/11": get_m_mediafile(3, 7),
                "meeting_mediafile/13": get_m_mediafile(
                    3,
                    8,
                    {
                        "projection_ids": [7],
                    },
                ),
                "mediafile/1": {"owner_id": "meeting/1", "meeting_mediafile_ids": [1]},
                "mediafile/2": {
                    "owner_id": "meeting/2",
                    "meeting_mediafile_ids": [2],
                    "child_ids": [3],
                },
                "mediafile/3": {
                    "parent_id": 2,
                    "owner_id": "meeting/2",
                    "meeting_mediafile_ids": [3],
                },
                "mediafile/4": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [4, 5],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": True,
                    "child_ids": [5],
                },
                "mediafile/5": {
                    "parent_id": 4,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [6, 7, 8],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/6": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [9],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": True,
                    "child_ids": [7],
                },
                "mediafile/7": {
                    "parent_id": 6,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [10, 11],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "child_ids": [8],
                },
                "mediafile/8": {
                    "parent_id": 7,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [12, 13],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/9": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [14],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        status_code, data = self.request(
            "get_mediafile_context", {"mediafile_ids": [1, 2, 4, 6, 7, 9]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "owner_id": "meeting/1",
                "published": False,
                "children_amount": 0,
                "meetings_of_interest": {
                    "1": {
                        "name": "Meeting 1",
                        "holds_attachments": True,
                        "holds_logos": True,
                        "holds_fonts": True,
                        "holds_current_projections": True,
                        "holds_history_projections": True,
                        "holds_preview_projections": False,
                    },
                },
            },
            "2": {
                "owner_id": "meeting/2",
                "published": False,
                "children_amount": 1,
                "meetings_of_interest": {
                    "2": {
                        "name": "Meeting 2",
                        "holds_attachments": True,
                        "holds_logos": False,
                        "holds_fonts": False,
                        "holds_current_projections": False,
                        "holds_history_projections": True,
                        "holds_preview_projections": True,
                    },
                },
            },
            "4": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 1,
                "meetings_of_interest": {
                    "1": {
                        "name": "Meeting 1",
                        "holds_attachments": False,
                        "holds_logos": False,
                        "holds_fonts": False,
                        "holds_current_projections": False,
                        "holds_history_projections": False,
                        "holds_preview_projections": True,
                    },
                    "2": {
                        "name": "Meeting 2",
                        "holds_attachments": False,
                        "holds_logos": True,
                        "holds_fonts": False,
                        "holds_current_projections": True,
                        "holds_history_projections": False,
                        "holds_preview_projections": False,
                    },
                    "3": {
                        "name": "Meeting 3",
                        "holds_attachments": True,
                        "holds_logos": False,
                        "holds_fonts": False,
                        "holds_current_projections": False,
                        "holds_history_projections": False,
                        "holds_preview_projections": False,
                    },
                },
            },
            "6": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 2,
                "meetings_of_interest": {
                    "2": {
                        "name": "Meeting 2",
                        "holds_attachments": False,
                        "holds_logos": False,
                        "holds_fonts": True,
                        "holds_current_projections": False,
                        "holds_history_projections": True,
                        "holds_preview_projections": False,
                    },
                    "3": {
                        "name": "Meeting 3",
                        "holds_attachments": True,
                        "holds_logos": True,
                        "holds_fonts": False,
                        "holds_current_projections": True,
                        "holds_history_projections": False,
                        "holds_preview_projections": False,
                    },
                },
            },
            "7": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 1,
                "meetings_of_interest": {
                    "2": {
                        "name": "Meeting 2",
                        "holds_attachments": False,
                        "holds_logos": False,
                        "holds_fonts": True,
                        "holds_current_projections": False,
                        "holds_history_projections": True,
                        "holds_preview_projections": False,
                    },
                    "3": {
                        "name": "Meeting 3",
                        "holds_attachments": False,
                        "holds_logos": False,
                        "holds_fonts": False,
                        "holds_current_projections": True,
                        "holds_history_projections": False,
                        "holds_preview_projections": False,
                    },
                },
            },
            "9": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 0,
                "meetings_of_interest": {},
            },
        }
