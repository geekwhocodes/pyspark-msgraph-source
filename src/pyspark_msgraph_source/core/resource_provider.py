from functools import lru_cache
import importlib
import logging
import pkgutil
from typing import Dict, Type
from pyspark_msgraph_source.core.base_client import BaseResourceProvider

# @lru_cache(maxsize=10)
def load_resource_providers() -> Dict[str, Type[BaseResourceProvider]]:
    """
    Dynamically loads all resource providers from the resources package
    """
    providers = {}
    root_package = __package__.split('.')[0]
    logging.debug(f"Current root package {root_package}.")
    
    package = f'{root_package}.resources'
    
    resources_pkg = importlib.import_module(package)
    
    for _, name, _ in pkgutil.iter_modules(resources_pkg.__path__):
        if name != 'base':  # Skip the base module
            try:
                module = importlib.import_module(f'{package}.{name}')
                for attr_name in dir(module):
                    if attr_name.endswith('ResourceProvider'):
                        provider_class = getattr(module, attr_name)
                        if (isinstance(provider_class, type) and 
                            issubclass(provider_class, BaseResourceProvider) and 
                            provider_class != BaseResourceProvider):
                            providers[name] = provider_class
            except ImportError as e:
                print(f"Warning: Could not load resource provider {name}: {e}")
    
    return frozenset(providers.items())

# @lru_cache(maxsize=10)
def get_resource_provider(resource_name: str, options: frozenset) -> BaseResourceProvider:
    """
    Factory method to get the appropriate resource provider
    """
    providers = dict(load_resource_providers())
    provider_class: BaseResourceProvider = providers.get(resource_name)
    
    if not provider_class:
        available = ', '.join(providers.keys())
        raise ValueError(
            f"Unsupported resource name: '{resource_name}'. "
            f"Available resources: {available}"
        )
    return provider_class(dict(options))