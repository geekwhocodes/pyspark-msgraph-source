from typing import Any, Dict, List, Union
from kiota_serialization_json.json_serialization_writer_factory import JsonSerializationWriterFactory
import json

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, BooleanType,
    ArrayType, TimestampType, DateType, LongType, BinaryType, DecimalType, DataType
)

from datetime import datetime, date
from decimal import Decimal

# Convert to JSON using Kiota
writer_factory = JsonSerializationWriterFactory()


def to_json(value: Any) -> Dict[str, Any]:
    """
    Serializes a Kiota serializable object to a JSON-compatible dictionary.

    Args:
        value (Any): An object that implements the Kiota serialization interface.

    Returns:
        dict: A dictionary representing the serialized JSON content.
    """
    writer = writer_factory.get_serialization_writer("application/json")
    value.serialize(writer)
    return json.loads(writer.get_serialized_content().decode("utf-8"))


def get_python_schema(
    obj: Any
) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Recursively extracts the schema from a Python object.

    Args:
        obj (Any): The Python object (e.g., dict, list, int, str) to analyze.

    Returns:
        Union[str, dict, list]: A nested schema representing the object's structure and field types.
            - For dicts: a dict with key-value schemas.
            - For lists: a list with the schema of the first element or "any" if empty.
            - For primitives: a string indicating the type ("str", "int", etc.).
    """
    if isinstance(obj, bool):
        return "bool"
    elif isinstance(obj, dict):
        return {key: get_python_schema(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        if obj:  # Assume first element type (homogeneous lists)
            return [get_python_schema(obj[0])]
        return ["any"]  # Empty lists default to "any"
    elif isinstance(obj, str):
        return "str"
    elif isinstance(obj, int):
        return "int"
    elif isinstance(obj, float):
        return "float"
    elif isinstance(obj, datetime):
        return "datetime"
    elif isinstance(obj, date):
        return "date"
    elif isinstance(obj, Decimal):
        return "decimal"
    elif obj is None:
        return "null"
    return "unknown"  # Fallback for unrecognized types


def to_pyspark_schema(
    schema_dict: Dict[str, Any]
) -> StructType:
    """
    Recursively converts a nested Python schema dictionary to a PySpark StructType schema.

    Args:
        schema_dict (dict): A dictionary with field names as keys and data types as values,
            where types are represented as strings (e.g., "str", "int", "bool").
            Nested dictionaries represent nested StructTypes.

    Returns:
        StructType: A PySpark StructType schema reflecting the provided structure.

    Example:
        Input:
            {"name": "str", "age": "int", "scores": ["float"], "address": {"city": "str"}}
        Output:
            StructType([
                StructField("name", StringType(), True),
                StructField("age", IntegerType(), True),
                StructField("scores", ArrayType(DoubleType()), True),
                StructField("address", StructType([
                    StructField("city", StringType(), True)
                ]), True)
            ])
    """
    type_mapping: Dict[str, DataType] = {
        "str": StringType(),
        "int": IntegerType(),
        "float": DoubleType(),
        "bool": BooleanType(),
        "datetime": TimestampType(),
        "date": DateType(),
        "long": LongType(),
        "binary": BinaryType(),
        "decimal": DecimalType(38, 18),
        "null": StringType(),
        "unknown": StringType(),
    }

    def convert_type(value: Any) -> DataType:
        """
        Recursively converts type descriptors to PySpark data types.

        Args:
            value (Any): The type descriptor (str, dict, list).

        Returns:
            DataType: The corresponding PySpark data type.
        """
        if isinstance(value, dict):  # Nested structure
            return StructType([StructField(k, convert_type(v), True) for k, v in value.items()])
        elif isinstance(value, list):  # List of elements (assume first element type)
            if not value:
                return ArrayType(StringType())  # Default to list of strings if empty
            return ArrayType(convert_type(value[0]))
        return type_mapping.get(value, StringType())  # Default to StringType

    struct_fields: List[StructField] = [
        StructField(field, convert_type(dtype), True) for field, dtype in schema_dict.items()
    ]
    return StructType(struct_fields)
