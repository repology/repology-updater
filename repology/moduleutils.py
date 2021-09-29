# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import importlib
import importlib.util
import inspect
import os
from typing import Any, Dict, Iterable, Optional, Type


__all__ = [
    'ClassFactory',
]


class ClassFactory:
    @staticmethod
    def _enumerate_all_submodules(module: str) -> Iterable[str]:
        spec = importlib.util.find_spec(module)
        if spec is None:
            raise RuntimeError('cannot find module {}'.format(module))
        if spec.submodule_search_locations is None:
            raise RuntimeError('module {} is not a package'.format(module))

        for location in spec.submodule_search_locations:
            for dirpath, dirnames, filenames in os.walk(location):
                for filename in filenames:
                    fullpath = os.path.join(dirpath, filename)
                    relpath = os.path.relpath(fullpath, location)

                    if not filename.endswith('.py'):
                        continue

                    yield '.'.join([module] + relpath[:-3].split(os.sep))

    def __init__(self, modulename: str, suffix: Optional[str] = None, superclass: Optional[Type[Any]] = None) -> None:
        self.classes: Dict[str, Any] = {}

        for submodulename in ClassFactory._enumerate_all_submodules(modulename):
            submodule = importlib.import_module(submodulename)
            for name, member in inspect.getmembers(submodule):
                if suffix is not None and not name.endswith(suffix):
                    continue

                try:  # workaround for https://bugs.python.org/issue45326
                    if superclass is not None and (not inspect.isclass(member) or not issubclass(member, superclass)):
                        continue
                except TypeError:
                    continue

                self.classes[name] = member

    def spawn(self, name: str, *args: Any, **kwargs: Any) -> Any:
        return self.classes[name](*args, **kwargs)

    def spawn_with_known_args(self, name: str, kwargs: Dict[str, Any]) -> Any:
        class_ = self.classes[name]

        filtered_kwargs = {
            key: value for key, value in kwargs.items() if key in inspect.getfullargspec(class_.__init__).args
        }

        return class_(**filtered_kwargs)
