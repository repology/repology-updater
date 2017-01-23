# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class PackageVersionClass:
    newest = 1
    outdated = 2
    ignored = 3


class RepositoryVersionClass:
    newest = 1
    outdated = 2
    mixed = 3
    ignored = 4
    lonely = 5


class Package:
    __slots__ = [
        'repo',
        'family',

        'name',
        'effname',

        'version',
        'origversion',
        'effversion',
        'versionclass',

        'maintainers',
        'category',
        'comment',
        'homepage',
        'licenses',
        'downloads',

        'ignore',
        'shadow',
        'ignoreversion',
    ]

    def __init__(self, **args):
        self.repo = None
        self.family = None

        self.name = None
        self.effname = None

        self.version = None
        self.origversion = None
        self.effversion = None
        self.versionclass = None

        self.maintainers = []
        self.category = None
        self.comment = None
        self.homepage = None
        self.licenses = []
        self.downloads = []

        self.ignore = False
        self.shadow = False
        self.ignoreversion = False

        for k, v in args.items():
            setattr(self, k, v)

    @property
    def __dict__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}
