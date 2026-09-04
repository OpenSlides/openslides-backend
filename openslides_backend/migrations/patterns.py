from typing import NewType, Union

_Table = NewType("_Table", str)

Table = Union[str, _Table]
Renames = tuple[dict[str, str], dict[str, dict[str, str]]]
