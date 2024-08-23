
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
                "meeting/1": {"mediafile_ids": [1], "meeting_mediafile_ids": [1]},
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
        self.set_models(
            {
                "meeting/1": {"mediafile_ids": [1], "meeting_mediafile_ids": [1, 4, 6]},
                "meeting/2": {
                    "mediafile_ids": [2, 3],
                    "meeting_mediafile_ids": [2, 3, 5, 7, 10, 11],
                },
                "meeting/3": {
                    "mediafile_ids": [],
                    "meeting_mediafile_ids": [8, 9, 11, 13],
                },
                "mediafile/1": {"owner_id": "meeting/1", "meeting_mediafile_ids": [1]},
                "meeting_mediafile/1": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                },
                "mediafile/2": {
                    "owner_id": "meeting/2",
                    "meeting_mediafile_ids": [2],
                    "child_ids": [3],
                },
                "meeting_mediafile/2": {
                    "meeting_id": 2,
                    "mediafile_id": 2,
                },
                "mediafile/3": {
                    "parent_id": 2,
                    "owner_id": "meeting/2",
                    "meeting_mediafile_ids": [3],
                },
                "meeting_mediafile/3": {
                    "meeting_id": 2,
                    "mediafile_id": 3,
                },
                "mediafile/4": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [4, 5],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": True,
                    "child_ids": [5],
                },
                "meeting_mediafile/4": {
                    "meeting_id": 1,
                    "mediafile_id": 4,
                },
                "meeting_mediafile/5": {
                    "meeting_id": 2,
                    "mediafile_id": 4,
                },
                "mediafile/5": {
                    "parent_id": 4,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [6, 7, 8],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/6": {
                    "meeting_id": 1,
                    "mediafile_id": 5,
                },
                "meeting_mediafile/7": {
                    "meeting_id": 2,
                    "mediafile_id": 5,
                },
                "meeting_mediafile/8": {
                    "meeting_id": 3,
                    "mediafile_id": 5,
                },
                "mediafile/6": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [9],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": True,
                    "child_ids": [7],
                },
                "meeting_mediafile/9": {
                    "meeting_id": 3,
                    "mediafile_id": 6,
                },
                "mediafile/7": {
                    "parent_id": 6,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [10, 11],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "child_ids": [8],
                },
                "meeting_mediafile/10": {
                    "meeting_id": 2,
                    "mediafile_id": 7,
                },
                "meeting_mediafile/11": {
                    "meeting_id": 3,
                    "mediafile_id": 7,
                },
                "mediafile/8": {
                    "parent_id": 7,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [12, 13],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/12": {
                    "meeting_id": 2,
                    "mediafile_id": 8,
                },
                "meeting_mediafile/13": {
                    "meeting_id": 3,
                    "mediafile_id": 8,
                },
                # TODO: Add projections, attachments and logo/font usages
            }
        )
        status_code, data = self.request(
            "get_mediafile_context", {"mediafile_ids": [1, 2, 4, 6, 7]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "owner_id": "meeting/1",
                "published": False,
                "children_amount": 0,
                "meetings_of_interest": {},
            },
            "2": {
                "owner_id": "meeting/2",
                "published": False,
                "children_amount": 1,
                "meetings_of_interest": {},
            },
            "4": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 1,
                "meetings_of_interest": {},
            },
            "6": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 2,
                "meetings_of_interest": {},
            },
            "7": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published": True,
                "children_amount": 1,
                "meetings_of_interest": {},
            },
        }
