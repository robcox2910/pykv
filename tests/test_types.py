"""Tests for value type handling and serialization."""

import pytest

from pykv.errors import SerializationError
from pykv.types import deserialize_value, serialize_value

EXPECTED_INT = 42
EXPECTED_FLOAT = 3.14


class TestSerializeValue:
    """Test serializing Python values to storable format."""

    def test_serialize_string(self) -> None:
        """Serialize a string value."""
        result = serialize_value("hello")
        assert result == {"type": "str", "data": "hello"}

    def test_serialize_int(self) -> None:
        """Serialize an integer value."""
        result = serialize_value(42)
        assert result == {"type": "int", "data": 42}

    def test_serialize_float(self) -> None:
        """Serialize a float value."""
        result = serialize_value(3.14)
        assert result == {"type": "float", "data": 3.14}

    def test_serialize_bool(self) -> None:
        """Serialize a boolean value."""
        result = serialize_value(True)
        assert result == {"type": "bool", "data": True}

    def test_serialize_none(self) -> None:
        """Serialize None."""
        result = serialize_value(None)
        assert result == {"type": "NoneType", "data": None}

    def test_serialize_list(self) -> None:
        """Serialize a list value."""
        result = serialize_value([1, 2, 3])
        assert result == {"type": "list", "data": [1, 2, 3]}

    def test_serialize_dict(self) -> None:
        """Serialize a dict value."""
        result = serialize_value({"a": 1})
        assert result == {"type": "dict", "data": {"a": 1}}

    def test_serialize_unsupported_type_raises(self) -> None:
        """Raise SerializationError for unsupported types."""
        with pytest.raises(SerializationError, match="Cannot serialize"):
            serialize_value(object())  # type: ignore[arg-type]


class TestDeserializeValue:
    """Test deserializing stored format back to Python values."""

    def test_deserialize_string(self) -> None:
        """Deserialize a string record."""
        result = deserialize_value({"type": "str", "data": "hello"})
        assert result == "hello"

    def test_deserialize_int(self) -> None:
        """Deserialize an integer record."""
        result = deserialize_value({"type": "int", "data": EXPECTED_INT})
        assert result == EXPECTED_INT

    def test_deserialize_float(self) -> None:
        """Deserialize a float record."""
        result = deserialize_value({"type": "float", "data": EXPECTED_FLOAT})
        assert result == EXPECTED_FLOAT

    def test_deserialize_bool(self) -> None:
        """Deserialize a boolean record."""
        result = deserialize_value({"type": "bool", "data": True})
        assert result is True

    def test_deserialize_none(self) -> None:
        """Deserialize a None record."""
        result = deserialize_value({"type": "NoneType", "data": None})
        assert result is None

    def test_deserialize_list(self) -> None:
        """Deserialize a list record."""
        result = deserialize_value({"type": "list", "data": [1, 2]})
        assert result == [1, 2]

    def test_deserialize_dict(self) -> None:
        """Deserialize a dict record."""
        result = deserialize_value({"type": "dict", "data": {"a": 1}})
        assert result == {"a": 1}

    def test_missing_type_key_raises(self) -> None:
        """Raise SerializationError when 'type' key is missing."""
        with pytest.raises(SerializationError, match="must contain"):
            deserialize_value({"data": "hello"})

    def test_missing_data_key_raises(self) -> None:
        """Raise SerializationError when 'data' key is missing."""
        with pytest.raises(SerializationError, match="must contain"):
            deserialize_value({"type": "str"})

    def test_unknown_type_raises(self) -> None:
        """Raise SerializationError for unknown type names."""
        with pytest.raises(SerializationError, match="Unknown type"):
            deserialize_value({"type": "set", "data": [1, 2]})

    def test_type_mismatch_raises(self) -> None:
        """Raise SerializationError when data does not match the declared type."""
        with pytest.raises(SerializationError, match="Expected data of type"):
            deserialize_value({"type": "int", "data": "not_a_number"})

    def test_non_string_type_raises(self) -> None:
        """Raise SerializationError when type is not a string."""
        with pytest.raises(SerializationError, match="Expected 'type' to be a string"):
            deserialize_value({"type": 123, "data": "hello"})


class TestRoundTrip:
    """Test serializing and then deserializing preserves the value."""

    @pytest.mark.parametrize(
        "value",
        [
            "hello",
            42,
            3.14,
            True,
            False,
            None,
            [1, "two", 3.0],
            {"nested": {"deep": True}},
        ],
        ids=["str", "int", "float", "true", "false", "none", "list", "dict"],
    )
    def test_round_trip(self, value: object) -> None:
        """Serialize and deserialize a value, expecting the same result."""
        record = serialize_value(value)  # type: ignore[arg-type]
        result = deserialize_value(record)
        assert result == value
