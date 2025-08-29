from base64 import b64encode

import yaml

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, InternalHelper
from openslides_backend.http.views.action_view import INTERNAL_AUTHORIZATION_HEADER
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.env import DEV_PASSWORD


def create_table_view(yml: str) -> None:
    GenerateCodeBlocks.models = InternalHelper.MODELS = yaml.safe_load(yml)
    (
        pre_code,
        table_name_code,
        view_name_code,
        alter_table_code,
        final_info_code,
        missing_handled_attributes,
        im_table_code,
        create_trigger_relationlistnotnull_code,
        create_trigger_unique_ids_pair_code,
        create_trigger_notify_code,
        errors,
    ) = GenerateCodeBlocks.generate_the_code()
    with get_new_os_conn() as conn:
        with conn.cursor() as curs:
            curs.execute(
                table_name_code + im_table_code + view_name_code + alter_table_code
            )


def b64encodes(value: str) -> str:
    """Returns the base64 encoded value as a string."""
    return b64encode(value.encode()).decode()


def get_internal_auth_header(password: str = DEV_PASSWORD) -> dict[str, str]:
    """Returns the internal auth header."""
    return {INTERNAL_AUTHORIZATION_HEADER: b64encodes(password)}
