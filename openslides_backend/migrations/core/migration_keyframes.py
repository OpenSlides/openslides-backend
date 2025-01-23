from collections import defaultdict
from dataclasses import dataclass

from openslides_backend.datastore.shared.postgresql_backend import (
    ConnectionHandler,
    apply_fields,
)
from openslides_backend.datastore.shared.util import BadCodingError
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    META_DELETED,
    META_POSITION,
    Collection,
    FullQualifiedId,
    Id,
    Position,
    collection_and_id_from_fqid,
    id_from_fqid,
)
from openslides_backend.shared.typing import Model

from .events import (
    BadEventException,
    BaseEvent,
    CreateEvent,
    DeleteEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)


class BaseMigrationKeyframeException(Exception):
    pass


class MigrationKeyframeModelDoesNotExist(BaseMigrationKeyframeException):
    pass


class MigrationKeyframeModelDeleted(BaseMigrationKeyframeException):
    pass


class MigrationKeyframeModelNotDeleted(BaseMigrationKeyframeException):
    pass


@dataclass
class RawKeyframeModel:
    data: Model
    deleted: bool


class MigrationKeyframeAccessor:
    def __init__(
        self,
        connection: ConnectionHandler,
        position: Position,
        migration_index: int,
        next_position: Position,
    ):
        self.connection = connection
        self.position = position
        self.migration_index = migration_index
        self.next_position = next_position

    def _fetch_model(self, fqid: FullQualifiedId) -> RawKeyframeModel | None:
        """
        Returns a RawKeyframeModel, if the model exists (created or deleted), so there
        was at least one create for this model.
        """
        raise NotImplementedError()

    def get_model(self, fqid: FullQualifiedId) -> Model:
        """Returns the model, if it exists and is not deleted."""
        model = self._fetch_model(fqid)
        if model is None:
            raise MigrationKeyframeModelDoesNotExist()
        if model.deleted:
            raise MigrationKeyframeModelDeleted()
        return model.data

    def get_deleted_model(self, fqid: FullQualifiedId) -> Model:
        """Returns the model, if it exists and is deleted."""
        model = self._fetch_model(fqid)
        if model is None:
            raise MigrationKeyframeModelDoesNotExist()
        if not model.deleted:
            raise MigrationKeyframeModelNotDeleted()
        return model.data

    def get_model_ignore_deleted(self, fqid: FullQualifiedId) -> tuple[Model, bool]:
        """Returns the model, if it exists regardless of the delete-state."""
        model = self._fetch_model(fqid)
        if model is None:
            raise MigrationKeyframeModelDoesNotExist()
        return (model.data, model.deleted)

    def model_exists(self, fqid: FullQualifiedId) -> bool:
        """regardless of the deleted-state"""
        return self._fetch_model(fqid) is not None

    def model_not_deleted(self, fqid: FullQualifiedId) -> bool:
        """Returns True if the model exists and is not deleted."""
        model = self._fetch_model(fqid)
        return model is not None and not model.deleted

    def get_all_ids_for_collection(self, collection: Collection) -> set[Id]:
        """only from not deleted models"""
        raise NotImplementedError()

    def apply_event(self, event: BaseEvent) -> None:
        """applies the event to this keyframe."""
        raise NotImplementedError()


class MigrationKeyframeModifier(MigrationKeyframeAccessor):
    def __init__(
        self,
        connection: ConnectionHandler,
        position: Position,
        migration_index: int,
        next_position: Position,
    ):
        super().__init__(connection, position, migration_index, next_position)

    def _create_model(self, fqid: FullQualifiedId, model: Model) -> None:
        """Creates a new model"""
        raise NotImplementedError()

    def _update_model(self, fqid: FullQualifiedId, model: RawKeyframeModel) -> None:
        """Updates model"""
        raise NotImplementedError()

    def apply_event(self, _event: BaseEvent) -> None:
        event = _event.clone()
        db_model = self._fetch_model(event.fqid)

        if isinstance(event, CreateEvent):
            if db_model is not None:
                raise BadEventException(f"Model {event.fqid} already exists")

            event_data = event.get_data()
            event_data[META_POSITION] = self.next_position
            event_data[META_DELETED] = False
            self._create_model(event.fqid, event_data)

        else:
            if db_model is None:
                raise BadEventException(f"Model {event.fqid} does not exist")

            db_model.data[META_POSITION] = self.next_position
            if isinstance(event, UpdateEvent):
                if db_model.deleted:
                    raise BadEventException(f"Model {event.fqid} is deleted")

                for k, v in event.get_data().items():
                    db_model.data[k] = v
                self._update_model(event.fqid, db_model)

            elif isinstance(event, DeleteFieldsEvent):
                if db_model.deleted:
                    raise BadEventException(f"Model {event.fqid} is deleted")

                for field in event.get_data():
                    db_model.data.pop(field, None)
                self._update_model(event.fqid, db_model)

            elif isinstance(event, ListUpdateEvent):
                if db_model.deleted:
                    raise BadEventException(f"Model {event.fqid} is deleted")

                modified_fields = apply_fields(db_model.data, event.add, event.remove)
                for k, v in modified_fields.items():
                    db_model.data[k] = v
                self._update_model(event.fqid, db_model)

            elif isinstance(event, DeleteEvent):
                if db_model.deleted:
                    raise BadEventException(f"Model {event.fqid} is deleted")

                db_model.data[META_DELETED] = True
                db_model.deleted = True
                self._update_model(event.fqid, db_model)

            else:
                raise BadCodingError()

    def keyframe_exists(self, position: Position, migration_index: int) -> bool:
        return self.connection.query_single_value(
            "select exists(select 1 from migration_keyframes where position=%s and migration_index=%s)",
            [position, migration_index],
        )

    def get_next_position(self) -> Position:
        """
        Searches for the next existent position and returns it.
        """
        return self.connection.query_single_value(
            "select min(position) from positions where position > %s", [self.position]
        )

    def move_to_next_position(self) -> None:
        """Takes this keyframe and move all data to the next position. Do not use
        this keyframe afterwards!"""
        raise NotImplementedError()


class DatabaseMigrationKeyframeModifier(MigrationKeyframeModifier):
    """
    This class represents a keyframe in the database. If `persistence` is False,
    all changes are applied in-memory and `move_to_next_position` is not available.
    Otherwise, the changes are applied to the database.
    """

    def __init__(
        self,
        connection: ConnectionHandler,
        position: Position,
        migration_index: int,
        next_position: Position,
        persistent: bool,
    ):
        if position <= 0:
            raise BadCodingError()

        super().__init__(connection, position, migration_index, next_position)
        self.persistent = persistent
        self.model_store: dict[FullQualifiedId, RawKeyframeModel] = {}
        self.created_collection_ids: dict[Collection, set[Id]] = defaultdict(set)
        self.deleted_collection_ids: dict[Collection, set[Id]] = defaultdict(set)
        self.keyframe_id: int = self.get_keyframe_id(
            connection, position, migration_index
        )

    @classmethod
    def get_keyframe_id(
        cls, connection: ConnectionHandler, position: Position, migration_index: int
    ) -> int:
        keyframe_id: int | None = connection.query_single_value(
            "select id from migration_keyframes where position=%s and migration_index=%s",
            [position, migration_index],
        )
        if keyframe_id is None:
            raise BadCodingError()
        return keyframe_id

    def get_all_ids_for_collection(self, collection: Collection) -> set[Id]:
        fqids = self.connection.query_list_of_single_values(
            "select fqid from migration_keyframe_models where keyframe_id=%s and fqid like %s",
            [self.keyframe_id, collection + KEYSEPARATOR + "%"],
        )
        ids = {id_from_fqid(fqid) for fqid in fqids}
        ids = (
            ids | self.created_collection_ids[collection]
        ) - self.deleted_collection_ids[collection]
        return ids

    def _fetch_model(self, fqid: FullQualifiedId) -> RawKeyframeModel | None:
        if not self.persistent:
            model = self.model_store.get(fqid)
            if model is not None:
                return model

        result = self.connection.query(
            "select data, deleted from migration_keyframe_models where keyframe_id=%s and fqid=%s",
            [self.keyframe_id, fqid],
        )
        if not result:
            return None
        return RawKeyframeModel(**result[0])

    def _create_model(self, fqid: FullQualifiedId, model: Model) -> None:
        if self.persistent:
            self.connection.execute(
                "insert into migration_keyframe_models (keyframe_id, fqid, data, deleted) values (%s, %s, %s, %s)",
                [self.keyframe_id, fqid, self.connection.to_json(model), False],
            )
        else:
            self.model_store[fqid] = RawKeyframeModel(data=model, deleted=False)
            collection, id = collection_and_id_from_fqid(fqid)
            self.created_collection_ids[collection].add(id)
            self.deleted_collection_ids[collection].discard(id)

    def _update_model(self, fqid: FullQualifiedId, model: RawKeyframeModel) -> None:
        if self.persistent:
            self.connection.execute(
                "update migration_keyframe_models set data=%s, deleted=%s where keyframe_id=%s and fqid=%s",
                [
                    self.connection.to_json(model.data),
                    model.deleted,
                    self.keyframe_id,
                    fqid,
                ],
            )
        else:
            self.model_store[fqid] = model
            collection, id = collection_and_id_from_fqid(fqid)
            if model.deleted:
                self.created_collection_ids[collection].discard(id)
                self.deleted_collection_ids[collection].add(id)
            else:
                self.created_collection_ids[collection].add(id)
                self.deleted_collection_ids[collection].discard(id)

    def move_to_next_position(self) -> None:
        if not self.persistent:
            raise BadCodingError()

        new_position = self.get_next_position()
        # Check, if there already exists a keyframe. If so, delete this one, since it is not needed anymore.
        if self.keyframe_exists(new_position, self.migration_index):
            self.connection.execute(
                "delete from migration_keyframes where id=%s",
                [self.keyframe_id],
            )
            return

        # Else: Modify the position of this keyframe
        self.connection.execute(
            "update migration_keyframes set position=%s where id=%s",
            [new_position, self.keyframe_id],
        )
