import sys
from typing import Any

from datastore.reader.core import GetAllRequest, GetRequest, Reader
from datastore.reader.services import register_services as register_reader_services
from datastore.shared.di import injector
from datastore.shared.util import DeletedModelsBehaviour, fqid_from_collection_and_id
from datastore.writer.core import RequestUpdateEvent, Writer, WriteRequest
from datastore.writer.services import register_services as register_writer_services

from openslides_backend.i18n.translator import Translator
from openslides_backend.models.models import Organization
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

collection_to_fields_map = {
    "organization": [
        "name",
        "login_text",
        "description",
    ],
    "meeting": [
        "name",
        "welcome_title",
        "welcome_text",
        "motion_preamble",
        "motions_export_title",
        "assignments_export_title",
        "users_pdf_welcometitle",
        "users_pdf_welcometext",
        "users_email_sender",
        "users_email_subject",
        "users_email_body",
    ],
    "group": ["name"],
    "motion_workflow": ["name"],
    "motion_state": ["name", "recommendation_label"],
    "projector_countdown": ["name"],
    "projector": ["name"],
    "motion": ["recommendation_label"],
}
possible_languages = Organization().default_language.constraints["enum"]


def read_collection(collection: str, fields: list[str]) -> Any:
    reader: Reader = injector.get(Reader)
    with reader.get_database_context():
        response = reader.get_all(
            GetAllRequest(
                collection, ["id", *fields], DeletedModelsBehaviour.NO_DELETED
            )
        )
    return response.items()


def check_language(language: str) -> None:
    if language not in possible_languages:
        print("language is not allowed.")
        print_help()
        sys.exit(2)


def check_organization_language() -> None:
    reader: Reader = injector.get(Reader)
    with reader.get_database_context():
        response = reader.get(GetRequest(ONE_ORGANIZATION_FQID, ["default_language"]))
    if response["default_language"] != "en":
        print("Cannot translate from source languages other than `en`.")
        print_help()
        sys.exit(3)


def print_help() -> None:
    print("Usage:  python translate.py <language>")
    print("     Translates from 'en' to <language>.")
    print(f"""     language could be '{"', '".join(possible_languages)}'.""")


def main() -> None:
    if len(sys.argv) != 2:
        print_help()
        sys.exit(1)

    language = sys.argv[1]
    check_language(language)
    Translator.set_translation_language(language)

    register_reader_services()
    register_writer_services()
    check_organization_language()

    # translate and generate events
    events = []
    for collection in collection_to_fields_map:
        fields = collection_to_fields_map[collection]
        for id_, model in read_collection(collection, fields):
            changed_fields: dict[str, Any] = {}
            for field in fields:
                old_value = model[field]
                possible_new_value = Translator.translate(old_value)
                if possible_new_value != old_value and possible_new_value is not None:
                    changed_fields[field] = possible_new_value
            if collection == "organization":
                changed_fields["default_language"] = language
            elif collection == "meeting":
                changed_fields["language"] = language
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
