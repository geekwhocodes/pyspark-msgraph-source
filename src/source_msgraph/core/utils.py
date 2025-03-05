from typing import Any
from kiota_serialization_json.json_serialization_writer_factory import JsonSerializationWriterFactory
import json

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, BooleanType,
    MapType, ArrayType, TimestampType, DateType, LongType, BinaryType, DecimalType
)

from datetime import datetime, date
from decimal import Decimal

# Convert to JSON using Kiota
writer_factory = JsonSerializationWriterFactory()
writer = writer_factory.get_serialization_writer("application/json")

def to_json(value):
    value.serialize(writer)
    # Get JSON string
    return json.loads((writer.get_serialized_content().decode("utf-8")))

def to_jsonValue(value):
    value.serialize(writer)
    # Get JSON string
    return str(json.loads((writer.get_serialized_content().decode("utf-8"))))



def get_python_schema(obj:Any):
    """
    Recursively extracts the schema from a Python object.

    :param obj: The Python object (dict, list, int, str, etc.).
    :return: A schema dictionary representing field types.
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

def to_pyspark_schema(schema_dict):
    """
    Recursively converts a nested Python schema dictionary to a PySpark StructType schema.

    :param schema_dict: Dictionary with field names as keys and data types as values.
    :return: PySpark StructType schema.
    """
    type_mapping = {
        "str": StringType(),
        "int": IntegerType(),
        "float": DoubleType(),
        "bool": BooleanType(),
        "datetime": TimestampType(),
        "date": DateType(),
        "long": LongType(),
        "binary": BinaryType(),
        "decimal": DecimalType(38, 18),
        "unknown": StringType()
    }

    def convert_type(value):
        """Recursively converts types, handling nested dicts and lists."""
        if isinstance(value, dict):  # Nested structure
            return StructType([StructField(k, convert_type(v), True) for k, v in value.items()])
        elif isinstance(value, list):  # List of elements (assume first element type)
            if not value:
                return ArrayType(StringType())  # Default to list of strings if empty
            return ArrayType(convert_type(value[0]))
        return type_mapping.get(value, StringType())  # Default to StringType

    struct_fields = [StructField(field, convert_type(dtype), True) for field, dtype in schema_dict.items()]
    return StructType(struct_fields)