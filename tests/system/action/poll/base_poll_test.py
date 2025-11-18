from typing import Any

from tests.system.action.base import BaseActionTestCase


class BasePollTestCase(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.vote_service.clear_all()

    def create_assignment(
        self, base: int, meeting_id: int, assignment_data: dict[str, Any] = {}
    ) -> None:
        self.set_models(
            {
                f"assignment/{base}": {
                    "title": "just do it",
                    "meeting_id": meeting_id,
                    **assignment_data,
                },
                f"list_of_speakers/{base + 100}": {
                    "content_object_id": f"assignment/{base}",
                    "meeting_id": meeting_id,
                },
            }
        )
