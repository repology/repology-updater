# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class PackageSanityCheckProblem(Exception):
    pass


class PackageSanityCheckFailure(PackageSanityCheckProblem):
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

        'extrafields',
    ]

    def __init__(self, repo=None, family=None, subrepo=None,
                 name=None, effname=None,
                 version=None, origversion=None, effversion=None, versionclass=None,
                 maintainers=None, category=None, comment=None, homepage=None, licenses=None, downloads=None,
                 ignore=False, shadow=False, ignoreversion=False,
                 extrafields=None):
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

        self.extrafields = extrafields if extrafields else {}

    def TryMerge(self, other):
        for slot in self.__slots__:
            self_val = getattr(self, slot)
            other_val = getattr(other, slot)

            if self_val is None or self_val == [] or self_val == {}:
                setattr(self, slot, other_val)
            elif other_val is None or other_val == [] or other_val == {}:
                pass
            elif self_val != other_val:
                return False

        return True

    def CheckSanity(self, transformed=True):
        # checks
        def NoNewlines(value):
            return 'contains newlines' if '\n' in value else ''

        def NoSlashes(value):
            return 'contains slashes' if '/' in value else ''

        def Stripped(value):
            return 'is not stripped' if value != value.strip() else ''

        def Alphanumeric(value):
            return 'contains not allowed symbols' if not re.fullmatch('[a-zA-Z0-9_-]+', value) else ''

        def Lowercase(value):
            return 'is not lowercase' if value != value.lower() else ''

        def NoWhitespace(value):
            return 'contains whitespace' if re.search('[ \t\n\r]', value) else ''

        def NonEmpty(value):
            return 'is empty' if value == '' else ''

        # checkers
        def CheckBool(value, name):
            if not isinstance(value, bool):
                raise PackageSanityCheckFailure('{}: {} is not a boolean'.format(self.name, name))

        def CheckStr(value, name, *checks):
            if not isinstance(value, str):
                raise PackageSanityCheckFailure('{}: {} is not a string'.format(self.name, name))
            for check in checks:
                result = check(value)
                if result:
                    raise PackageSanityCheckProblem('{}: {} {}: "{}"'.format(self.name, name, result, value))

        def CheckList(value, name, *checks):
            if not isinstance(value, list):
                raise PackageSanityCheckFailure('{}: {} is not a list'.format(self.name, name))
            for element in value:
                CheckStr(element, name, *checks)

        def CheckDict(value, name, *checks):
            if not isinstance(value, dict):
                raise PackageSanityCheckFailure('{}: {} is not a dict'.format(self.name, name))
            for element in value.values():
                CheckStr(element, name, *checks)

        CheckStr(self.repo, 'repo', NoNewlines, Stripped, Alphanumeric, Lowercase)
        CheckStr(self.family, 'family', NoNewlines, Stripped, Alphanumeric, Lowercase)
        if self.subrepo is not None:
            CheckStr(self.subrepo, 'subrepo', NoNewlines, Stripped)

        CheckStr(self.name, 'name', NoNewlines, Stripped, NonEmpty)
        if transformed or self.effname is not None:
            CheckStr(self.effname, 'effname', NoNewlines, Stripped, NonEmpty, NoSlashes)

        CheckStr(self.version, 'version', NoNewlines, Stripped, NonEmpty)
        if self.origversion is not None:
            CheckStr(self.origversion, 'origversion', NoNewlines, Stripped)

        CheckList(self.maintainers, 'maintainers', NoNewlines, Stripped, NoWhitespace, NoSlashes, NonEmpty)
        if self.category is not None:
            CheckStr(self.category, 'category', NoNewlines, Stripped, NonEmpty)
        if self.comment is not None:
            CheckStr(self.comment, 'comment', NoNewlines, Stripped, NonEmpty)
        if self.homepage is not None:
            CheckStr(self.homepage, 'homepage', NoWhitespace, NonEmpty)
        CheckList(self.licenses, 'licenses', NoNewlines, Stripped, NonEmpty)
        CheckList(self.downloads, 'downloads', NoWhitespace, NoNewlines, NonEmpty)

        CheckBool(self.ignore, 'ignore')
        CheckBool(self.shadow, 'shadow')
        CheckBool(self.ignoreversion, 'ignoreversion')

        CheckDict(self.extrafields, 'extrafields', NoWhitespace, NonEmpty)

    def Normalize(self):
        # normalize homepage (currently adds / to url which points to host)
        if self.homepage:
            match = re.fullmatch('(https?://)([^/]+)(/.*)?', self.homepage, re.IGNORECASE)

            if match:
                schema = match.group(1).lower()
                hostname = match.group(2).lower()
                path = match.group(3) or '/'

                self.homepage = schema + hostname + path

        # unicalize and sort maintainers list
        if len(self.maintainers) > 1:
            self.maintainers = sorted(set(self.maintainers))

    def CheckFormat(self):
        # check
        for slot in self.__slots__:
            if not hasattr(self, slot):
                return False

        return True

    @property
    def __dict__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}
