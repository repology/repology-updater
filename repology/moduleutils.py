# Copyright (C) 2017-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


__all__ = [
    'ModuleEnumerator',
    'ClassFactory',
]


class ModuleEnumerator:
    def __init__(self, pkgname, pkgfile):
        self.modules = []

        pkgdir = os.path.dirname(pkgfile)

        for modfile in os.listdir(pkgdir):
            modname = inspect.getmodulename(os.path.join(pkgdir, modfile))
            if modname and modname != '__init__':
                self.modules.append(importlib.import_module(pkgname + '.' + modname))

    def Enumerate(self):
        for module in self.modules:
            yield module


class ClassFactory:
    @staticmethod
    def enumerate_all_submodules(module):
        for location in importlib.util.find_spec(module).submodule_search_locations:
            for dirpath, dirnames, filenames in os.walk(location):
                for filename in filenames:
                    fullpath = os.path.join(dirpath, filename)
                    relpath = os.path.relpath(fullpath, location)

                    if not filename.endswith('.py'):
                        continue

                    yield '.'.join([module] + relpath[:-3].split(os.sep))

    def __init__(self, modulename, suffix=None, superclass=None):
        self.classes = {}

        for submodulename in self.enumerate_all_submodules(modulename):
            submodule = importlib.import_module(submodulename)
            for name, member in inspect.getmembers(submodule):
                suitable = True

                if suffix is not None:
                    suitable &= name.endswith(suffix)

                if superclass is not None:
                    suitable &= inspect.isclass(member) and issubclass(member, superclass)

                if suitable:
                    self.classes[name] = member

    def Spawn(self, name, *args, **kwargs):
        return self.classes[name](*args, **kwargs)

    def SpawnWithKnownArgs(self, name, kwargs):
        class_ = self.classes[name]

        filtered_kwargs = {
            key: value for key, value in kwargs.items() if key in inspect.getfullargspec(class_.__init__).args
        }

        return class_(**filtered_kwargs)
