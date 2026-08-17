from ....shared.typing import Schema

meeting_poll_default_schema: Schema = {
    "allow_abstain": {"type": "boolean"},
    "allow_nota": {"type": "boolean"},
    "display_chart": {"type": "string"},
    "group_ids": {
        "type": "array",
        "items": {"type": "integer"},
        "uniqueItems": True,
    },
    "onehundred_percent_base": {"type": "string"},
    "sort_result_by_votes": {"type": "boolean"},
    "strike_out": {"type": "boolean"},
    "visibility": {"type": "string"},
}
