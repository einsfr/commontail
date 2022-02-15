import importlib
import re

from types import ModuleType
from typing import List, Optional, Dict, Any


__all__ = ['import_settings', ]


def import_settings(import_to: dict, modules: List[str], installed_apps: Optional[List[str]] = None,
                    merge: Optional[List[str]] = None, root: Optional[str] = None,
                    default_module: Optional[str] = None) -> None:
    """
    Imports settings from applications, environment-defined and other modules

    Modules list can use:
    - simple python submodules in 'root' module: 'common' or 'com.mon'
    - default settings modules from installed applications, filtered by regular expression - these are starting with '@'
      symbol: '@common' - 'common' will be used as regular expression to search for matching application name
    Every modules list item can be marked with '*' symbol making it optional. If such module can't be imported -
    no exception will be raised. Order of '@' and '*' symbols in the beginning of module is unimportant - first two
    symbols are always checked for presence of both of them.

    Example (using in Django settings module):
    import_settings(
        globals(), ['@home', 'common', APP_ENV, f'*{APP_ENV}_local'], INSTALLED_APPS,
        ['INSTALLED_APPS', 'STATICFILES_DIRS'], str(__name__)
    ) will result in loading:
        - home.default_settings
        - __name__.common
        - __name__.{APP_ENV}
        - __name__.{APP_ENV}_local (optional)

    :param import_to: destination dictionary, usually globals() in test_settings.py file
    :param modules: list of imported modules ids
    :param installed_apps: installed applications list
    :param merge: parameters to be merged instead of replace
    :param root: root path to search for modules, None if modules are imported by full path
    :param default_module: default module name to search for application's settings, 'default_settings' if None passed
    :return: None
    """
    if installed_apps is None:
        installed_apps = []
    if merge is None:
        merge = []

    processed_modules: List[str] = []
    if not default_module:
        default_module = 'default_settings'

    def _recursive_merge(source: Dict[str, Any], destination: Dict[str, Any], is_root: bool = True) -> None:
        k: str
        v: Any
        for k, v in source.items():
            if k in destination:
                if isinstance(v, dict) and isinstance(destination[k], dict):
                    _recursive_merge(v, destination[k], False)
                elif is_root and k in merge:
                    destination[k] = destination[k] + v
                else:
                    destination[k] = v
            else:
                destination[k] = v

    def _import_by_name(module_name: str, optional: bool) -> None:
        if module_name in processed_modules:
            return

        processed_modules.append(module_name)

        try:
            imported_module: ModuleType = importlib.import_module(module_name)
        except ImportError:
            if optional:
                return
            else:
                raise

        s_name: str
        module_settings: Dict[str, Any] = dict(
            [(s_name, getattr(imported_module, s_name)) for s_name in dir(imported_module) if s_name.isupper()]
        )
        _recursive_merge(module_settings, import_to)

    def _import_by_app_re(module_name: str, optional: bool) -> None:
        if not installed_apps:
            raise RuntimeError('Installed applications list is empty - can\'t use "@id" in modules list.')

        import_list: List[str] = [
            f'{app}.{default_module}' for app in installed_apps if re.match(module_name, app)
        ]

        if not import_list:
            return

        i: str
        for i in import_list:
            _import_by_name(i, optional)

    module_id: str
    for module_id in modules:
        if not module_id:
            raise ValueError('Module id can\'t be empty')

        mode_part: str = module_id[:2] if len(module_id) > 2 else module_id[:1] if len(module_id) == 2 else ''
        opt: bool = False
        app_re: bool = False
        if mode_part:
            opt = '*' in mode_part
            app_re = '@' in mode_part
            module_id = module_id[opt + app_re:]

        if app_re:
            _import_by_app_re(module_id, opt)
        else:
            _import_by_name(f'{root}.{module_id}' if root else module_id, opt)
