from ....shared.typing import Schema

meeting_poll_default_schema: Schema = {
    "allow_live_voting": {"type": "boolean"},
    "default_live_voting_enabled": {"type": "boolean"},
    "default_method": {"type": "string"},
    "default_required_majority": {"type": "string"},
    "enable_cumulative_voting": {"type": "boolean"},
    "enable_max_options_limit": {"type": "boolean"},
    "enable_max_yes_votes": {"type": "boolean"},
    "group_ids": {
        "type": "array",
        "items": {"type": "integer"},
        "uniqueItems": True,
    },
    "onehundred_percent_base": {"type": "string"},
    "sort_result_by_votes": {"type": "boolean"},
    "visibility": {"type": "string"},
}
