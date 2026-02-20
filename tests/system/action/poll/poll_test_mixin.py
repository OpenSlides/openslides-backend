from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase
from tests.system.base import ADMIN_PASSWORD, ADMIN_USERNAME, DEFAULT_PASSWORD


class PollTestMixin(BaseActionTestCase):
    def start_poll(self, id: int) -> None:
        self.vote_service.start(id)

    def prepare_users_and_poll(self, user_count: int) -> list[int]:
        user_ids = list(range(2, user_count + 2))
        self.create_meeting()
        self.create_motion(1, 1)
        self.set_models(
            {
                "poll/1": {
                    "content_object_id": "motion/1",
                    "type": Poll.TYPE_NAMED,
                    "pollmethod": "YNA",
                    "backend": "fast",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "onehundred_percent_base": "YNA",
                    "title": "Poll 1",
                },
                "option/1": {"meeting_id": 1, "poll_id": 1},
                **{f"user/{i}": {**self._get_user_data(f"user{i}")} for i in user_ids},
                **{
                    f"meeting_user/{i+10}": {"meeting_id": 1, "user_id": i}
                    for i in user_ids
                },
                "group/3": {
                    "meeting_user_ids": [id_ + 10 for id_ in user_ids],
                    "poll_ids": [1],
                },
                "meeting/1": {"present_user_ids": user_ids},
            }
        )
        self.start_poll(1)
        for i in user_ids:
            self.client.login(f"user{i}", DEFAULT_PASSWORD)
            response = self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
            self.assert_status_code(response, 200)
        self.client.login(ADMIN_USERNAME, ADMIN_PASSWORD)
        return user_ids
