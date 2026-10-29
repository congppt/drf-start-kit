from importlib import import_module
from pkgutil import iter_modules

urlpatterns = []

for module_info in sorted(iter_modules(__path__), key=lambda module: module.name):
    if module_info.ispkg:
        continue
    module = import_module(f"{__name__}.{module_info.name}")
    urlpatterns.extend(getattr(module, "urlpatterns", []))
