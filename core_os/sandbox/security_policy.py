from typing import Set

class SecurityPolicy:
    """
    Defines the security policy for the sandboxed environment,
    specifically which modules are allowed to be imported.
    """
    def __init__(self):
        # Default safe modules
        self._allowed_modules: Set[str] = {
            'math', 'datetime', 'json', 're', 'collections', 'itertools',
            'functools', 'string', 'time', 'uuid', 'os', 'sys', 'psutil',
            'subprocess'
        }

    def is_module_allowed(self, module_name: str) -> bool:
        """Checks if a top-level module is in the allowlist."""
        # Handle submodules (e.g., 'os.path' -> check 'os')
        root_module = module_name.split('.')[0]
        return root_module in self._allowed_modules

    def add_allowed_module(self, module_name: str):
        """Adds a module to the allowlist."""
        self._allowed_modules.add(module_name)
