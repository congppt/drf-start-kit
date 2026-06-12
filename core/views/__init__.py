from importlib import import_module
from pkgutil import iter_modules

url_patterns = []

for module_info in sorted(iter_modules(__path__), key=lambda module: module.name):
    if module_info.ispkg:
        continue
    module = import_module(f'{__name__}.{module_info.name}')
    url_patterns.extend(getattr(module, 'url_patterns', []))
