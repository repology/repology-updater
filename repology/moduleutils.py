# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
    def __init__(self, pkgname, pkgfile, suffix):
        self.modules = {}

        for module in ModuleEnumerator(pkgname, pkgfile).Enumerate():
            for name, member in inspect.getmembers(module):
                if name.endswith(suffix) and inspect.isclass(member):
                    self.modules[name[:-len(suffix)]] = member

    def Spawn(self, name, kwargs):
        class_ = self.modules[name]

        filtered_kwargs = {
            key: value for key, value in kwargs.items() if key in inspect.getfullargspec(class_.__init__).args
        }

        return class_(**filtered_kwargs)
