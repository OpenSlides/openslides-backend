from ...shared.patterns import Collection


class GetManyRequest:
    """
    Encapsulates a single GetManyRequest to be used for get_many requests to the
    database.
    """

    mapped_fields: set[str]

    def __init__(
        self,
        collection: Collection,
        ids: list[int],
        mapped_fields: set[str] | list[str] | None = None,
    ) -> None:
        self.collection = collection
        self.ids = ids
        if isinstance(mapped_fields, list):
            self.mapped_fields = set(mapped_fields)
        else:
            self.mapped_fields = mapped_fields or set()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, GetManyRequest)
            and self.collection == other.collection
            and self.ids == other.ids
            and self.mapped_fields == other.mapped_fields
        )

    def __repr__(self) -> str:
        return str(
            {
                "collection": self.collection,
                "ids": self.ids,
                "mapped_fields": list(self.mapped_fields),
            }
        )
