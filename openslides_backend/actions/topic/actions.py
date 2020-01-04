from typing import List, Optional

from ...utils.types import Event
from .. import register_action
from ..base import DatabaseAction
from ..types import Payload
from .schema import is_valid_new_topic


@register_action("topic.create")
class TopicCreate(DatabaseAction):
    def validate(self, payload: Payload) -> None:
        is_valid_new_topic(payload)

    def read_database(self, payload: Payload) -> List[str]:
        return []

    def create_event(self, payload: Payload, keys: Optional[List[str]] = None) -> Event:
        pass


# class TopicViewSet(ViewSet):
#     """
#     Viewset for topics.
#     """
#
#     def dispatch(self, request: Request, **kwargs: dict) -> Response:
#         """
#         Dispatches request to the viewpoint.
#         """
#         if not request.is_json:
#             raise BadRequest(
#                 "Wrong media type. Use 'Content-Type: application/json' instead."
#             )
#         return getattr(self, self.viewpoint)(request, **kwargs)
#
#     def new(self, request: Request, **kwargs: dict) -> Response:
#         """
#         Viewpoint to create new topics.
#         """
#         # Parse event id.
#         event_id = kwargs["event"]
#
#         # Check permissions.
#         # TODO
#
#         # Check existence of event in database.
#         # It someone removes it right this moment, this is no problem.
#         # event = self.database.get(f"event:{event_id}:exists")
#         # if event is None:
#         #    raise BadRequest(f"Event with id {event_id} does not exist.")
#
#         # Validate payload.
#         payload = request.json
#         is_valid_new_topic(payload)
#         result = []
#
#         # Set lock to prepare data for event store.
#         with self.locker.acquire(f"{event_id}.topics.new"):
#             # Get highest existing id.
#             topic_id = self.event_store.get_highest_id("topic")
#             data = {}
#
#             # import time
#
#             # time.sleep(25)
#
#             # Parse topics.
#             for topic in payload:
#                 topic_id += 1
#                 data.update(
#                     {
#                         f"topic:{topic_id}:exists": True,
#                         f"topic:{topic_id}:title": topic["title"],
#                         f"topic:{topic_id}:event": event_id,
#                         f"topic:{topic_id}:text": topic.get("text", ""),
#                         f"topic:{topic_id}:attachments": topic.get("attachments", []),
#                     }
#                 )
#                 result.append(topic_id)
#
#             # Save topics.
#             self.event_store.save(data)
#
#         # Send topics to stream and create response.
#         self.event_store.send(data)
#         return Response(json.dumps(result), status=201, content_type="application/json")
#
#     def update(self, request: Request, **kwargs: dict) -> Response:
#         """
#         Viewpoint to update existing topics.
#         """
#         # TODO: Check permissions.
#         data = request.json
#         is_valid_update_topic(data)
#         result = {"updated": 0, "error": 0}
#         # for topic in data:
#         #     id = topic.pop("id")
#         #     rev = topic.pop("rev")
#         #     url = "/".join((self.database_url, id))
#         #     headers = self.database_headers
#         #     headers["If-Match"] = rev
#         #     response = requests.put(url, data=json.dumps(topic), headers=headers)
#         #     if response.ok:
#         #         result["updated"] += 1
#         #     else:
#         #         result["error"] += 1
#         return Response(json.dumps(result), status=200, content_type="application/json")
#
#     def delete(self, request: Request, **kwargs: dict) -> Response:
#         """
#         Viewpoint to delete existing topics.
#         """
#         return Response("Hello")
#
#
# def get_get_rules_func(environment: Environment) -> Callable[[Map], Iterable[Rule]]:
#     """
#     Contructor for Werkzeug's get_rules method.
#     """
#
#     def get_rules(map: Map) -> Iterable[Rule]:
#         """
#         Rules for this app.
#         """
#         return [
#             Rule(
#                 "/<int:event>/topics/new",
#                 endpoint="TopicViewSet new",
#                 methods=("POST",),
#                 view=TopicViewSet("new", environment=environment),
#             ),
#             Rule(
#                 "/<int:event>/topics/update",
#                 endpoint="TopicViewSet update",
#                 methods=("POST",),
#                 view=TopicViewSet("update", environment=environment),
#             ),
#             Rule(
#                 "/<int:event>/topics/delete",
#                 endpoint="TopicViewSet delete",
#                 methods=("POST",),
#                 view=TopicViewSet("delete", environment=environment),
#             ),
#         ]
#
#     return get_rules
