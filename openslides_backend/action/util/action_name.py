from .typing import Payload


def summarize_action_names(payload: Payload) -> str:
    result = ",".join(elem.get("action", "") for elem in payload)
    if len(result) > 256:
        action_names = result.split(",")
        result = ""
        prev_action_name = action_names[0]
        counter = 1
        for action_name in action_names[1:]:
            if action_name == prev_action_name:
                counter += 1
            else:
                result += f"{prev_action_name}_{counter},"
                prev_action_name = action_name
                counter = 1
        result += f"{prev_action_name}_{counter}"
        if len(result) > 256:
            result = result[:255] + "…"
    return result
