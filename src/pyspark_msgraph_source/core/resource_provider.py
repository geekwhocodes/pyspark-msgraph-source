from functools import lru_cache
import importlib
import logging
import pkgutil
from typing import Dict, Type
from pyspark_msgraph_source.core.base_client import BaseResourceProvider


# @lru_cache(maxsize=10)
def load_resource_providers() -> Dict[str, Type[BaseResourceProvider]]:
    """
    Dynamically loads all resource providers from the `resources` package.

    This function scans the `resources` subpackage of the current root package,
    discovers all modules (excluding `base.py`), and imports any classes ending
    with `ResourceProvider` that are subclasses of `BaseResourceProvider`.

    This allows dynamic discovery and registration of new resource providers
    without requiring explicit imports.

    Returns:
        Dict[str, Type[BaseResourceProvider]]: A dictionary mapping resource
        names (module names) to their corresponding resource provider classes.

    Example:
        providers = load_resource_providers()
        print(providers.keys())
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

    return providers


# @lru_cache(maxsize=10)
def get_resource_provider(resource_name: str, options: frozenset) -> BaseResourceProvider:
    """
    Factory method to retrieve the appropriate resource provider based on its name.

    This function looks up the resource provider class registered in
    `load_resource_providers()`, instantiates it with the provided options,
    and returns the instance.

    Args:
        resource_name (str): The name of the resource (typically the module name).
        options (frozenset): A frozenset of key-value pairs representing the
            configuration options for the provider.

    Returns:
        BaseResourceProvider: An instance of the corresponding resource provider.

    Raises:
        ValueError: If the requested resource name is not found in the
            available providers.

    Example:
        provider = get_resource_provider('users', frozenset({'tenant_id': 'xxx'}.items()))
        for record in provider.iter_records():
            print(record)
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
