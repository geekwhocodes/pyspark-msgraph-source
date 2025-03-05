from functools import lru_cache
import importlib
import pkgutil
from typing import Dict, Type
from source_msgraph.core.base_client import BaseResourceProvider


def load_resource_providers() -> Dict[str, Type[BaseResourceProvider]]:
    """
    Dynamically loads all resource providers from the resources package
    """
    providers = {}
    package = 'source_msgraph.resources'
    
    # Import the resources package
    resources_pkg = importlib.import_module(package)
    
    # Iterate through all submodules
    for _, name, _ in pkgutil.iter_modules(resources_pkg.__path__):
        if name != 'base':  # Skip the base module
            try:
                # Import the module
                module = importlib.import_module(f'{package}.{name}')
                # Look for *ResourceProvider class
                for attr_name in dir(module):
                    if attr_name.endswith('ResourceProvider'):
                        provider_class = getattr(module, attr_name)
                        if (isinstance(provider_class, type) and 
                            issubclass(provider_class, BaseResourceProvider) and 
                            provider_class != BaseResourceProvider):
                            providers[name] = provider_class
            except ImportError as e:
                print(f"Warning: Could not load resource provider {name}: {e}")
    
    return providers

def get_resource_provider(resource_name: str, options: Dict[str, str]) -> BaseResourceProvider:
    """
    Factory method to get the appropriate resource provider
    """
    providers = load_resource_providers()
    provider_class: BaseResourceProvider = providers.get(resource_name)
    
    if not provider_class:
        available = ', '.join(providers.keys())
        raise ValueError(
            f"Unsupported resource name: '{resource_name}'. "
            f"Available resources: {available}"
        )
    return provider_class(options)