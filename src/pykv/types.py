"""Value type handling and serialization for PyKV.

Imagine you have a backpack where you can store different things: books
(strings), calculators (numbers), lists (shopping lists), and folders
(dictionaries). This module makes sure every item is properly wrapped
before storing and properly unwrapped when you take it out.

Supported types: str, int, float, list, dict, bool, and None.
"""

import json

from pykv.errors import SerializationError

# The types that PyKV can store -- like the items allowed in your backpack.
StorableValue = str | int | float | list[object] | dict[str, object] | bool | None

# Map from type name string to actual Python type for deserialization.
_TYPE_NAME_MAP: dict[str, type[object]] = {
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "bool": bool,
    "NoneType": type(None),
}


def serialize_value(value: StorableValue) -> dict[str, object]:
    """Convert a Python value into a dictionary that can be saved as JSON.

    Think of this like putting a label on a box before storing it.
    The label says what type of item is inside (string, number, list, etc.)
    so you know how to unpack it later.

    Args:
        value: The value to serialize. Must be a supported type.

    Returns:
        A dictionary with "type" and "data" keys.

    Raises:
        SerializationError: If the value type is not supported.

    """
    type_name = type(value).__name__
    if type_name not in _TYPE_NAME_MAP:
        msg = f"Cannot serialize value of type {type_name!r}. Supported types: {', '.join(_TYPE_NAME_MAP)}"
        raise SerializationError(msg)

    try:
        # Round-trip through JSON to ensure the value is fully serializable.
        data = json.loads(json.dumps(value))
    except (TypeError, ValueError) as exc:
        msg = f"Cannot serialize value: {exc}"
        raise SerializationError(msg) from exc

    return {"type": type_name, "data": data}


def deserialize_value(record: dict[str, object]) -> StorableValue:
    """Convert a serialized dictionary back into a Python value.

    This is like reading the label on a box and unpacking the item
    inside so you can use it again.

    Args:
        record: A dictionary with "type" and "data" keys.

    Returns:
        The original Python value.

    Raises:
        SerializationError: If the record is malformed or the type is unknown.

    """
    if "type" not in record or "data" not in record:
        msg = "Record must contain 'type' and 'data' keys"
        raise SerializationError(msg)

    type_name = record["type"]
    if not isinstance(type_name, str):
        msg = f"Expected 'type' to be a string, got {type(type_name).__name__}"
        raise SerializationError(msg)

    if type_name not in _TYPE_NAME_MAP:
        msg = f"Unknown type {type_name!r}. Supported types: {', '.join(_TYPE_NAME_MAP)}"
        raise SerializationError(msg)

    data = record["data"]

    # For None, just return None regardless of what data says.
    if type_name == "NoneType":
        return None

    expected_type = _TYPE_NAME_MAP[type_name]
    if not isinstance(data, expected_type):
        msg = f"Expected data of type {type_name}, got {type(data).__name__}"
        raise SerializationError(msg)

    return data  # type: ignore[return-value]
