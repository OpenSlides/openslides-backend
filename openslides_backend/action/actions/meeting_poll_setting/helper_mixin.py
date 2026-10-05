from ....shared.typing import Schema

meeting_poll_setting_schema: Schema = {
    "allow_live_voting": {"type": "boolean"},
    "group_ids": {
        "type": "array",
        "items": {"type": "integer"},
        "uniqueItems": True,
    },
    "enable_cumulative_voting": {"type": "boolean"},
    "enable_live_voting": {"type": "boolean"},
    "enable_max_options_limit": {"type": "boolean"},
    "enable_max_yes_votes": {"type": "boolean"},
    "method": {"type": "string"},
    "onehundred_percent_base": {"type": "string"},
    "required_majority": {"type": "string"},
    "sort_result_by_votes": {"type": "boolean"},
    "visibility": {"type": "string"},
}
