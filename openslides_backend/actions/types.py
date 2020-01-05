from typing import Any, Dict, List

from mypy_extensions import TypedDict

Payload = List[Dict[str, Any]]

DataSet = TypedDict("DataSet", {"position": int, "data": Any})
