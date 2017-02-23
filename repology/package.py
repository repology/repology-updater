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
        'subrepo',

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

    def __init__(self, repo=None, family=None, subrepo=None,
                 name=None, effname=None,
                 version=None, origversion=None, effversion=None, versionclass=None,
                 maintainers=None, category=None, comment=None, homepage=None, licenses=None, downloads=None,
                 ignore=False, shadow=False, ignoreversion=False):
        self.repo = repo
        self.family = family
        self.subrepo = subrepo

        self.name = name
        self.effname = effname

        self.version = version
        self.origversion = origversion
        self.effversion = effversion
        self.versionclass = versionclass

        self.maintainers = maintainers if maintainers else []
        self.category = category
        self.comment = comment
        self.homepage = homepage
        self.licenses = licenses if licenses else []
        self.downloads = downloads if downloads else []

        self.ignore = ignore
        self.shadow = shadow
        self.ignoreversion = ignoreversion

    @property
    def __dict__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}
