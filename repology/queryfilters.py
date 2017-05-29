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


class QueryFilter():
    def GetWhere(self):
        return None

    def GetWhereArgs(self):
        return []

    def GetHaving(self):
        return None

    def GetHavingArgs(self):
        return []

    def GetSort(self):
        return None


class NameStartingQueryFilter(QueryFilter):
    def __init__(self, name=None):
        self.name = name

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return 'effname >= %s' if self.name else 'true'

    def GetWhereArgs(self):
        return [self.name] if self.name else []

    def GetSort(self):
        return 'effname ASC'

    def ApplyToRequest(self, req):
        req.NameStarting(self.name)


class NameAfterQueryFilter(QueryFilter):
    def __init__(self, name=None):
        self.name = name

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return 'effname > %s' if self.name else 'true'

    def GetWhereArgs(self):
        return [self.name] if self.name else []

    def GetSort(self):
        return 'effname ASC'

    def ApplyToRequest(self, req):
        req.NameAfter(self.name)


class NameBeforeQueryFilter(QueryFilter):
    def __init__(self, name=None):
        self.name = name

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return 'effname < %s' if self.name else 'true'

    def GetWhereArgs(self):
        return [self.name] if self.name else []

    def GetSort(self):
        return 'effname DESC'

    def ApplyToRequest(self, req):
        req.NameBefore(self.name)


class NameSubstringQueryFilter(QueryFilter):
    def __init__(self, name):
        self.name = name.lower()  # XXX: need to normalize like effnames

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return '{table}.effname like %s'

    def GetWhereArgs(self):
        return ['%' + self.name + '%']

    def ApplyToRequest(self, req):
        req.NameSubstring(self.name)


class MaintainerQueryFilter(QueryFilter):
    def __init__(self, maintainer):
        self.maintainer = maintainer

    def GetTable(self):
        return 'maintainer_metapackages'

    def GetWhere(self):
        return '{table}.maintainer=%s'

    def GetWhereArgs(self):
        return [self.maintainer]

    def ApplyToRequest(self, req):
        req.Maintainer(self.maintainer)


class MaintainerOutdatedQueryFilter(QueryFilter):
    def __init__(self, maintainer):
        self.maintainer = maintainer

    def GetTable(self):
        return 'maintainer_metapackages'

    def GetWhere(self):
        return '{table}.maintainer=%s and {table}.num_packages_outdated > 0'

    def GetWhereArgs(self):
        return [self.maintainer]

    def ApplyToRequest(self, req):
        req.OutdatedForMaintainer(self.maintainer)


class InRepoQueryFilter(QueryFilter):
    def __init__(self, repo):
        self.repo = repo

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return '{table}.repo=%s'

    def GetWhereArgs(self):
        return [self.repo]

    def ApplyToRequest(self, req):
        req.InRepo(self.repo)


class InAnyRepoQueryFilter(QueryFilter):
    def __init__(self, repos):
        self.repos = repos

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return '{table}.repo in (' + ','.join(['%s'] * len(self.repos)) + ')'

    def GetWhereArgs(self):
        return [repo for repo in self.repos]

    def ApplyToRequest(self, req):
        req.InAnyRepo(self.repos)


class InNumFamiliesQueryFilter(QueryFilter):
    def __init__(self, more=None, less=None):
        self.more = more
        self.less = less

    def GetTable(self):
        return 'metapackage_repocounts'

    def GetWhere(self):
        conditions = []
        if self.more is not None:
            conditions.append('{table}.num_families >= %s')
        if self.less is not None:
            conditions.append('{table}.num_families <= %s')

        return ' AND '.join(conditions)

    def GetWhereArgs(self):
        args = []
        if self.more is not None:
            args.append(self.more)
        if self.less is not None:
            args.append(self.less)

        return args

    def ApplyToRequest(self, req):
        if self.more is not None:
            req.MoreFamilies(self.more)
        if self.less is not None:
            req.LessFamilies(self.less)


class OutdatedInRepoQueryFilter(QueryFilter):
    def __init__(self, repo):
        self.repo = repo

    def GetTable(self):
        return 'repo_metapackages'

    def GetWhere(self):
        return '{table}.repo=%s AND {table}.num_outdated>0'

    def GetWhereArgs(self):
        return [self.repo]

    def ApplyToRequest(self, req):
        req.OutdatedInRepo(self.repo)


class NotInRepoQueryFilter(QueryFilter):
    def __init__(self, repo):
        self.repo = repo

    def GetTable(self):
        return 'repo_metapackages'

    def GetHaving(self):
        return 'count(nullif({table}.repo = %s, false)) = 0'

    def GetHavingArgs(self):
        return [self.repo]

    def ApplyToRequest(self, req):
        req.NotInRepo(self.repo)
