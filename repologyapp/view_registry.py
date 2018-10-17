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
import inspect
import os


def _enumerate_modules(pkgname, pkgfile):
    pkgdir = os.path.dirname(pkgfile)

    for modfile in os.listdir(pkgdir):
        modname = inspect.getmodulename(os.path.join(pkgdir, modfile))
        if modname and modname != '__init__':
            yield importlib.import_module(pkgname + '.' + modname)


class ViewRegistry():
    def __init__(self, pkgname, pkgfile):
        self.registrants = []

        for module in _enumerate_modules(pkgname, pkgfile):
            for name, member in inspect.getmembers(module):
                if isinstance(member, ViewRegistrant):
                    self.registrants.append(member)

    def RegisterInFlask(self, app):
        for registrant in self.registrants:
            registrant.RegisterInFlask(app)


class ViewRegistrar():
    def __init__(self, route, **options):
        self.route = route
        self.options = options

    def __call__(self, f):
        return ViewRegistrant(f, self.route, self.options)


class ViewRegistrant():
    def __init__(self, f, route, options):
        if isinstance(f, ViewRegistrant):
            # allow nesting
            self.f = f.f
            self.next = f
        else:
            self.f = f
            self.next = None
        self.route = route
        self.options = options

    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def RegisterInFlask(self, app):
        app.add_url_rule(self.route, self.f.__name__, self.f, **self.options)
        if self.next is not None:
            self.next.RegisterInFlask(app)
