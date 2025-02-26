import importlib

def resolve_resource_class(resource_path: str):
    """Resolve the appropriate resource handler based on the resource path."""
    parts = resource_path.split('/')
    module_name = "source_msgraph"

    for depth in range(min(len(parts), 5)):  # Limit depth to 5
        module_name += f".{parts[depth]}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "ResourceHandler"):
                return module.ResourceHandler
        except ModuleNotFoundError:
            continue  # Try next level
    
    # TODO: Implement BaseResource if required at all
    raise ValueError(f"No handler found for resource: {resource_path}")
