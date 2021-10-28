from typing import Any

from openslides_backend.models.base import model_registry


def assure_model_in_registry(model: Any) -> None:
    collection = model.collection
    if collection not in model_registry:
        model_registry[collection] = model


def assure_model_rm_from_registry(model: Any) -> None:
    collection = model.collection
    if collection in model_registry:
        del model_registry[collection]
