from typing import Any


def test_simple(write, finalize, assert_model):
    test_data: dict[str, dict[str, Any]] = {
        "projector/1": {"scroll": -1},
        "projector/2": {"scroll": 0},
        "projector/3": {"scroll": 1},
        "projector/4": {"scroll": -1},
    }

    write(
        *[
            {"type": "create", "fqid": fqid, "fields": data}
            for fqid, data in test_data.items()
        ]
    )
    write({"type": "delete", "fqid": "projector/4"})

    finalize("0076_projector_scroll_minimum")

    test_data["projector/1"]["scroll"] = 0
    test_data["projector/4"]["meta_deleted"] = True

    for fqid, model in test_data.items():
        assert_model(fqid, model)
