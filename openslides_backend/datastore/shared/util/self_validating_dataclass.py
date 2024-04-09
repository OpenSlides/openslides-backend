from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Optional, TypeAlias, Union, get_args, get_origin, get_type_hints

from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedField,
    FullQualifiedId,
    Id,
    Position,
)

from .exceptions import BadCodingError, InvalidFormat
from .key_types import (
    assert_is_collection,
    assert_is_field,
    assert_is_fqfield,
    assert_is_fqid,
    assert_is_id,
)

custom_types: list[TypeAlias] = [
    Collection,
    Field,
    Id,
    FullQualifiedId,
    FullQualifiedField,
    Position,
]

optional_custom_types: dict[TypeAlias, TypeAlias] = {
    t: Optional[t] for t in custom_types
}


@dataclass
class SelfValidatingDataclass:
    """
    A self-validating dataclass. Reads the type hints from the subclass and validates
    the values accordingly. Supports collection, field, fqid, id and position,
    Optional[<supported_type>] and List[<supported_type>].
    """

    def __post_init__(self):
        for key, type_hint in get_type_hints(self).items():
            value = getattr(self, key)
            if value is not None:
                self.validate_nested_types(type_hint, value)

    def validate_nested_types(self, type_hint: type, value: Any) -> None:
        origin = get_origin(type_hint)
        type_hint = self.normalize_type_hint(type_hint)
        if origin == Union:
            if type_hint in custom_types:
                self.validate(value, type_hint)
            else:
                nested_types = get_args(type_hint)
                errors = []
                for nested_type in nested_types:
                    try:
                        self.validate_nested_types(nested_type, value)
                        break
                    except AssertionError:
                        pass
                    except InvalidFormat as e:
                        errors.append(e)
                else:
                    if not len(errors):
                        raise BadCodingError(
                            dedent(
                                """
                            Given type does not match the type annotation.
                            Value: %s
                            Type hint: %s"
                            """
                            )
                            % (value, type_hint)
                        )
                    elif len(errors) == 1:
                        raise errors[0]
                    else:
                        raise InvalidFormat(
                            "The following errors occurred when trying to validate the\
                                data: %s"
                            % errors
                        )
        elif origin == list:
            nested_type = get_args(type_hint)[0]
            if not get_origin(nested_type):
                assert all(isinstance(el, nested_type) for el in value)
            for el in value:
                self.validate(el, nested_type)

    def normalize_type_hint(self, type_hint: type) -> type:
        for t, opt_t in optional_custom_types.items():
            if opt_t == type_hint:
                return t
        return type_hint

    def validate(self, value: Any, type: type) -> None:
        if type == Collection:
            assert_is_collection(value)
        elif type == Field:
            assert_is_field(value)
        elif type == Id:
            assert_is_id(str(value))
        elif type == FullQualifiedId:
            assert_is_fqid(value)
        elif type == FullQualifiedField:
            assert_is_fqfield(value)
        elif type == Position:
            if value <= 0:
                raise InvalidFormat("The position has to be >0")
