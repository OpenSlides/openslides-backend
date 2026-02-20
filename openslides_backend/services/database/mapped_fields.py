# from collections import defaultdict
from openslides_backend.shared.exceptions import InvalidFormat
from openslides_backend.shared.patterns import Collection, Field, FullQualifiedId

# Postgres only supports 1664 columns per query, so choose a number below that
MAX_UNIQUE_FIELDS_PER_QUERY = 1000


class MappedFields:
    """
    Container class for mapped fields and all related data. Only automatically calculated field is
    `needs_whole_model`, all other fields have to be set by the user.
    """

    unique_fields: list[Field]
    collections: list[Collection]
    fqids: list[FullQualifiedId]
    needs_whole_model: bool

    def __init__(self, mapped_fields: list[Field] = []) -> None:
        self.validate_mapped_fields(mapped_fields)
        self.unique_fields = mapped_fields
        self.collections = []
        self.post_init()

    def post_init(self) -> None:
        self.needs_whole_model = (
            len(self.unique_fields) == 0
            or len(self.unique_fields) > MAX_UNIQUE_FIELDS_PER_QUERY
        )

    def validate_mapped_fields(self, mapped: list[Field] = []) -> None:
        invalid_fields = []
        for field in mapped:
            if field is None or " " in field:
                invalid_fields.append(field)
        if invalid_fields:
            raise InvalidFormat(f"Invalid fields: {invalid_fields}")
