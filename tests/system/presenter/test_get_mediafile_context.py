from typing import Any, Literal

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

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
        self.create_meeting()
        self.create_mediafile(1, 1)
        self.set_models(
            {
                "meeting_mediafile/1": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "access_group_ids": None,
                    "inherited_access_group_ids": None,
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
                **additional_data,
            }

        self.create_meeting(meeting_data={"name": "Meeting 1"})
        self.create_meeting(4, meeting_data={"name": "Meeting 4", "committee_id": 60})
        self.create_meeting(7, meeting_data={"name": "Meeting 7", "committee_id": 60})

        self.create_topic(1, 1)
        self.create_topic(2, 4)
        self.create_topic(3, 7)
        self.create_topic(4, 1)

        self.create_mediafile(1, 1)
        self.create_mediafile(2, 4)
        self.create_mediafile(3, 4, parent_id=2)
        self.create_mediafile(4)
        self.create_mediafile(5, parent_id=4)
        self.create_mediafile(6)
        self.create_mediafile(7, parent_id=6)
        self.create_mediafile(8, parent_id=7)
        self.create_mediafile(9)

        self.set_models(
            {
                "meeting/1": {
                    "logo_projector_header_id": 1,
                    "font_bold_italic_id": 1,
                },
                "group/2": {
                    "meeting_mediafile_access_group_ids": [4],
                    "meeting_mediafile_inherited_access_group_ids": [4, 6],
                },
                "projection/1": get_projection(1, 1, 1, "history"),
                "projection/2": get_projection(1, 4, 1, "preview"),
                "projector/2": {"meeting_id": 1},
                "projection/8": get_projection(1, 1, 2, "current"),
                "meeting_mediafile/1": get_m_mediafile(
                    1,
                    1,
                    {
                        "is_public": True,
                        "attachment_ids": ["topic/1", "topic/4"],
                    },
                ),
                "meeting_mediafile/4": get_m_mediafile(1, 4),
                "meeting_mediafile/6": get_m_mediafile(1, 5),
                "meeting/4": {
                    "logo_web_header_id": 7,
                    "font_monospace_id": 10,
                },
                "group/5": {
                    "meeting_mediafile_access_group_ids": [2, 5, 14],
                    "meeting_mediafile_inherited_access_group_ids": [
                        2,
                        3,
                        5,
                        7,
                        10,
                        12,
                        14,
                    ],
                },
                "projection/3": get_projection(4, 2, 4, "history"),
                "projection/4": get_projection(4, 3, 4, "preview"),
                "projection/5": get_projection(4, 7, 4, "current"),
                "projection/6": get_projection(4, 12, 4, "history"),
                "meeting_mediafile/2": get_m_mediafile(4, 2),
                "meeting_mediafile/3": get_m_mediafile(
                    4, 3, {"attachment_ids": ["topic/2"]}
                ),
                "meeting_mediafile/5": get_m_mediafile(4, 4),
                "meeting_mediafile/7": get_m_mediafile(4, 5),
                "meeting_mediafile/10": get_m_mediafile(4, 7),
                "meeting_mediafile/12": get_m_mediafile(4, 8),
                "meeting_mediafile/14": get_m_mediafile(4, 9),
                "meeting/7": {"logo_pdf_header_r_id": 9},
                "group/8": {
                    "meeting_mediafile_access_group_ids": [9],
                    "meeting_mediafile_inherited_access_group_ids": [8, 9, 11, 13],
                },
                "projection/7": get_projection(7, 13, 7, "current"),
                "meeting_mediafile/8": get_m_mediafile(
                    7, 5, {"attachment_ids": ["topic/3"]}
                ),
                "meeting_mediafile/9": get_m_mediafile(
                    7, 6, {"attachment_ids": ["topic/3"]}
                ),
                "meeting_mediafile/11": get_m_mediafile(7, 7),
                "meeting_mediafile/13": get_m_mediafile(7, 8),
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
                "owner_id": "meeting/4",
                "published": False,
                "children_amount": 1,
                "meetings_of_interest": {
                    "4": {
                        "name": "Meeting 4",
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
                    "4": {
                        "name": "Meeting 4",
                        "holds_attachments": False,
                        "holds_logos": True,
                        "holds_fonts": False,
                        "holds_current_projections": True,
                        "holds_history_projections": False,
                        "holds_preview_projections": False,
                    },
                    "7": {
                        "name": "Meeting 7",
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
                    "4": {
                        "name": "Meeting 4",
                        "holds_attachments": False,
                        "holds_logos": False,
                        "holds_fonts": True,
                        "holds_current_projections": False,
                        "holds_history_projections": True,
                        "holds_preview_projections": False,
                    },
                    "7": {
                        "name": "Meeting 7",
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
                    "4": {
                        "name": "Meeting 4",
                        "holds_attachments": False,
                        "holds_logos": False,
                        "holds_fonts": True,
                        "holds_current_projections": False,
                        "holds_history_projections": True,
                        "holds_preview_projections": False,
                    },
                    "7": {
                        "name": "Meeting 7",
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
