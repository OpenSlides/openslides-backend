import sys
from typing import Any, Dict, List

from datastore.reader.core import FilterRequest, Reader
from datastore.reader.services import register_services as register_reader_services
from datastore.shared.di import injector
from datastore.shared.util import FilterOperator, fqid_from_collection_and_id
from datastore.writer.core import RequestUpdateEvent, Writer, WriteRequest
from datastore.writer.services import register_services as register_writer_services

from openslides_backend.locale.translator import Translator

collection_to_fields_map = {
    "group": ["name"],
    "motion_workflow": ["name"],
    "motion_state": ["name", "recommendation_label"],
    "projector_countdown": ["name"],
    "projector": ["name"],
    "meeting": [
        "welcome_title",
        "welcome_text",
        "name",
        "description",
        "users_email_subject",
        "users_email_body",
        "assignments_export_title",
    ],
}


def read_collection(collection: str, fields: List[str]) -> Any:
    reader: Reader = injector.get(Reader)
    with reader.get_database_context():
        response = reader.filter(
            FilterRequest(
                collection,
                FilterOperator("meta_deleted", "=", False),
                ["id", *fields],
            )
        )
    return response["data"].items()


def print_help() -> None:
    print("Usage:  python translate.py <language>")
    print("     Translates from en to <language>.")
    print("     language could be de, en, it, es, ru, cs")


def main() -> None:
    if len(sys.argv) != 2:
        print_help()
        sys.exit(1)

    language = sys.argv[1]
    Translator.set_translation_language(language)

    register_reader_services()
    register_writer_services()

    # translate and generate events
    events = []
    for collection in collection_to_fields_map:
        fields = collection_to_fields_map[collection]
        for id_, model in read_collection(collection, fields):
            changed_fields: Dict[str, Any] = {}
            for field in fields:
                old_value = model[field]
                possible_new_value = Translator.translate(old_value)
                if possible_new_value != old_value and possible_new_value is not None:
                    changed_fields[field] = possible_new_value
            if changed_fields:
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id(collection, id_),
                        changed_fields,
                    )
                )

    # write events into the datastore
    if events:
        write_request = WriteRequest(events, None, 0, {})  # type: ignore
        writer: Writer = injector.get(Writer)
        writer.write([write_request], log_all_modified_fields=False)


if __name__ == "__main__":
    main()
