from ....shared.typing import Schema

meeting_projector_default_object_list = [
    "agenda_all_items",
    "topics",
    "list_of_speakers",
    "current_list_of_speakers",
    "motion",
    "amendment",
    "motion_block",
    "assignment",
    "user",
    "mediafile",
    "projector_message",
    "projector_countdowns",
    "assignment_poll",
    "motion_poll",
    "poll",
]

used_as_default_for_schema: Schema = {
    "description": "Replacements for all default projector-objects in meeting",
    "type": "object",
    "properties": {
        name: {"type": ["integer", "null"]}
        for name in meeting_projector_default_object_list
    },
    "additionalProperties": False,
}
