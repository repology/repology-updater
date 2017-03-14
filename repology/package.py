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


import re


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


class PackageMergeConflict(Exception):
    pass


class PackageSanityCheckFailure(Exception):
    pass


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

    def IsMergeable(self, other):
        for slot in self.__slots__:
            self_val = getattr(self, slot)
            other_val = getattr(other, slot)

            if self_val is not None and self_val != [] and other_val is not None and other_val != [] and self_val != other_val:
                return False

        return True

    def Merge(self, other):
        for slot in self.__slots__:
            self_val = getattr(self, slot)
            other_val = getattr(other, slot)

            if self_val is None or self_val == []:
                setattr(self, slot, other_val)
            elif other_val is None or other_val == []:
                setattr(self, slot, self_val)
            elif self_val != other_val:
                raise PackageMergeConflict('{}: {} != {}'.format(self.name, self_val, other_val))

    def CheckSanity(self):
        def CheckStr(value, name, no_newlines=False, no_whitespace=False, non_empty=False, stripped=False, alphanumeric=False, lowercase=False):
            if not isinstance(value, str):
                raise PackageSanityCheckFailure('{}: {} is not a string'.format(self.name, name))
            if no_newlines and '\n' in value:
                raise PackageSanityCheckFailure('{}: {} contains newlines: "{}"'.format(self.name, name, value))
            if stripped and value != value.strip():
                raise PackageSanityCheckFailure('{}: {} not stripped: "{}"'.format(self.name, name, value))
            if alphanumeric and re.match('[^a-zA-Z0-9_-]', value):
                raise PackageSanityCheckFailure('{}: {} contains not allowed symbols: "{}"'.format(self.name, name, value))
            if lowercase and value != value.lower():
                raise PackageSanityCheckFailure('{}: {} not lowercase: "{}"'.format(self.name, name, value))
            if no_whitespace and (' ' in value or '\t' in value or '\n' in value or '\r' in value):
                raise PackageSanityCheckFailure('{}: {} contains whitespace: "{}"'.format(self.name, name, value))
            if non_empty and value == '':
                raise PackageSanityCheckFailure('{}: {} is empty'.format(self.name, name))

        def CheckList(value, name, no_newlines=False, no_whitespace=False, non_empty=False, stripped=False, alphanumeric=False, lowercase=False):
            if not isinstance(value, list):
                raise PackageSanityCheckFailure('{}: {} is not a list'.format(self.name, name))
            for subvalue in value:
                CheckStr(subvalue, name, no_newlines=no_newlines, no_whitespace=no_whitespace, non_empty=non_empty, stripped=stripped, alphanumeric=alphanumeric, lowercase=lowercase)

        CheckStr(self.repo, 'repo', no_newlines=True, stripped=True, alphanumeric=True, lowercase=True)
        CheckStr(self.family, 'family', no_newlines=True, stripped=True, alphanumeric=True, lowercase=True)
        if self.subrepo is not None:
            CheckStr(self.subrepo, 'subrepo', no_newlines=True, stripped=True, alphanumeric=True, lowercase=True)

        CheckStr(self.name, 'name', no_newlines=True, stripped=True)
        if self.effname is not None:
            CheckStr(self.effname, 'effname', no_newlines=True, stripped=True)

        CheckStr(self.version, 'version', no_newlines=True, stripped=True)
        if self.origversion is not None:
            CheckStr(self.origversion, 'origversion', no_newlines=True, stripped=True)

        CheckList(self.maintainers, 'maintainers', no_newlines=True, stripped=True)
        if self.category is not None:
            CheckStr(self.category, 'category', no_newlines=True, stripped=True)
        if self.comment is not None:
            CheckStr(self.comment, 'comment', no_newlines=True, stripped=True)
        if self.homepage is not None:
            CheckStr(self.homepage, 'homepage', no_whitespace=True)
        CheckList(self.licenses, 'licenses', no_newlines=True, stripped=True)
        CheckList(self.downloads, 'downloads', no_whitespace=True)

    def Normalize(self):
        if self.homepage:
            if re.match('https?://[^/]+$', self.homepage):
                self.homepage = self.homepage + '/'

        if self.maintainers:
            self.maintainers = sorted(set(self.maintainers))

    @property
    def __dict__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}
