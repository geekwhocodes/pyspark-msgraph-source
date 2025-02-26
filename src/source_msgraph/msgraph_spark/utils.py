from kiota_serialization_json.json_serialization_writer_factory import JsonSerializationWriterFactory
import json
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