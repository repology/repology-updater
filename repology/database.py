# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json

import psycopg2

from repology.package import Package


class Query:
    def __init__(self, query=None, *args):
        self.parts = [query] if query else []
        self.args = list(args)

    def GetQuery(self):
        return ' '.join(filter(None.__ne__, self.parts))

    def GetArgs(self):
        return self.args

    def Append(self, other, *args):
        if isinstance(other, str):
            self.parts += [other]
            self.args += list(args)
        else:
            self.parts.append(other.GetQuery())
            self.args += other.GetArgs()
        return self

    def __bool__(self):
        return not not self.parts


class AndQuery(Query):
    def __init__(self, query=None, *args):
        Query.__init__(self, query, *args)

    def GetQuery(self):
        if not self.parts:
            return None
        return ' AND '.join(map(lambda x: '(' + x + ')', filter(None.__ne__, self.parts)))


class OrQuery(Query):
    def __init__(self, query=None, *args):
        Query.__init__(self, query, *args)

    def GetQuery(self):
        if not self.parts:
            return None
        return ' OR '.join(map(lambda x: '(' + x + ')', filter(None.__ne__, self.parts)))


class MetapackageRequest:
    def __init__(self):
        # effname filtering
        self.namecond = None
        self.namebound = None
        self.nameorder = None

        self.name_substring = None

        # maintainer (maintainer_metapackages)
        self.maintainer = None
        self.maintainer_outdated = False

        # num families (metapackage_repocounts)
        self.minfamilies = None
        self.maxfamilies = None

        # repos (repo_metapackages)
        self.inrepo = None
        self.notinrepo = None

        # category
        self.category = None

        # flags
        self.newest = None
        self.outdated = None
        self.newest_single_repo = None
        self.newest_single_family = None
        self.problematic = None

        # other
        self.limit = None

    def Bound(self, bound):
        if not bound:
            pass
        elif bound.startswith('..'):
            self.NameTo(bound[2:])
        else:
            self.NameFrom(bound)

    def NameFrom(self, name):
        if self.namecond:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.namecond = '>='
            self.namebound = name
        self.nameorder = 'ASC'

    def NameTo(self, name):
        if self.namecond:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.namecond = '<='
            self.namebound = name
        self.nameorder = 'DESC'

    def NameSubstring(self, substring):
        if self.name_substring:
            raise RuntimeError('duplicate effname substring condition')
        self.name_substring = substring

    def Maintainer(self, maintainer):
        if self.maintainer:
            raise RuntimeError('duplicate maintainer condition')
        self.maintainer = maintainer

    def InRepo(self, repo):
        if self.inrepo:
            raise RuntimeError('duplicate repository condition')

        self.inrepo = repo

    def NotInRepo(self, repo):
        if self.notinrepo:
            raise RuntimeError('duplicate not-in-repository condition')
        self.notinrepo = repo

    def Category(self, category):
        if self.category:
            raise RuntimeError('duplicate category condition')
        self.category = category

    def MinFamilies(self, num):
        if self.minfamilies:
            raise RuntimeError('duplicate more families condition')
        self.minfamilies = num

    def MaxFamilies(self, num):
        if self.maxfamilies:
            raise RuntimeError('duplicate less families condition')
        self.maxfamilies = num

    def Limit(self, limit):
        if self.limit:
            raise RuntimeError('duplicate limit')
        self.limit = limit

    def Newest(self):
        self.newest = True

    def Outdated(self):
        self.outdated = True

    def Problematic(self):
        self.problematic = True

    def NewestSingleFamily(self):
        self.newest_single_family = True

    def NewestSingleRepo(self):
        self.newest_single_repo = True

    def GetQuery(self):
        tables = set()
        where = AndQuery()
        having = AndQuery()

        newest_handled = False
        outdated_handled = False
        problematic_handled = False

        # table joins and conditions
        if self.maintainer:
            tables.add('maintainer_metapackages')
            where.Append('maintainer_metapackages.maintainer = %s', self.maintainer)
            if self.newest:
                where.Append('maintainer_metapackages.num_packages_newest > 0 OR maintainer_metapackages.num_packages_devel > 0')
                newest_handled = True
            if self.outdated:
                outdated_handled = True
                where.Append('maintainer_metapackages.num_packages_outdated > 0')
            if self.problematic:
                problematic_handled = True
                where.Append('maintainer_metapackages.num_packages_ignored > 0 OR maintainer_metapackages.num_packages_incorrect > 0 OR maintainer_metapackages.num_packages_untrusted > 0')

        if self.minfamilies:
            tables.add('metapackage_repocounts')
            where.Append('metapackage_repocounts.num_families >= %s', self.minfamilies)

        if self.maxfamilies:
            tables.add('metapackage_repocounts')
            where.Append('metapackage_repocounts.num_families <= %s', self.maxfamilies)

        if self.inrepo:
            tables.add('repo_metapackages')
            where.Append('repo_metapackages.repo = %s', self.inrepo)
            if self.newest:
                where.Append('repo_metapackages.num_packages_newest > 0 OR repo_metapackages.num_packages_devel > 0')
                newest_handled = True
            if self.outdated:
                where.Append('repo_metapackages.num_packages_outdated > 0')
                outdated_handled = True
            if self.problematic:
                problematic_handled = True
                where.Append('repo_metapackages.num_packages_ignored > 0 OR repo_metapackages.num_packages_incorrect > 0 OR repo_metapackages.num_packages_untrusted > 0')

        if self.notinrepo:
            tables.add('repo_metapackages as repo_metapackages1')
            having.Append('count(*) FILTER (WHERE repo_metapackages1.repo = %s) = 0', self.notinrepo)

        if self.category:
            tables.add('category_metapackages')
            where.Append('category_metapackages.category = %s', self.category)

        if self.newest_single_family:
            tables.add('metapackage_repocounts')
            where.Append('metapackage_repocounts.num_families_newest = 1')

        if self.newest_single_repo:
            tables.add('metapackage_repocounts')
            where.Append('metapackage_repocounts.num_repos_newest = 1')

        if self.newest and not newest_handled:
            tables.add('repo_metapackages')
            where.Append('repo_metapackages.num_packages_newest > 0 OR repo_metapackages.num_packages_devel > 0')

        if self.outdated and not outdated_handled:
            tables.add('repo_metapackages')
            where.Append('repo_metapackages.num_packages_outdated > 0')

        if self.problematic and not problematic_handled:
            tables.add('repo_metapackages')
            where.Append('repo_metapackages.num_packages_ignored > 0 OR repo_metapackages.num_packages_incorrect > 0 OR repo_metapackages.num_packages_untrusted > 0')

        # effname conditions
        if self.namecond and self.namebound:
            where.Append('effname ' + self.namecond + ' %s', self.namebound)

        if self.name_substring:
            where.Append('effname LIKE %s', '%' + self.name_substring + '%')

        # construct query
        query = Query('SELECT DISTINCT effname FROM')
        query.Append(tables.pop() if tables else 'repo_metapackages')
        for table in tables:
            query.Append('INNER JOIN ' + table + ' USING(effname)')

        if where:
            query.Append('WHERE').Append(where)

        if having:
            query.Append('GROUP BY effname HAVING').Append(having)

        if self.nameorder:
            query.Append('ORDER BY effname ' + self.nameorder)
        else:
            query.Append('ORDER BY effname ASC')

        if self.limit:
            query.Append('LIMIT %s', self.limit)

        return (query.GetQuery(), query.GetArgs())


class Database:
    def __init__(self, dsn, querymgr, readonly=True, autocommit=False, application_name=None):
        self.db = psycopg2.connect(dsn, application_name=application_name)
        self.db.set_session(readonly=readonly, autocommit=autocommit)
        querymgr.InjectQueries(self, self.db)
        self.queries = self  # XXX: switch to calling queries directly and remove

    def RequestManyAsSingleColumnArray(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            return [row[0] for row in cursor.fetchall()]

    def RequestManyAsDicts(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            names = [desc.name for desc in cursor.description]

            return [dict(zip(names, row)) for row in cursor.fetchall()]

    def commit(self):
        self.db.commit()

    def RequestManyAsPackages(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            names = [desc.name for desc in cursor.description]

            return [Package(**dict(zip(names, row))) for row in cursor.fetchall()]

    def AddPackages(self, packages):
        with self.db.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO packages(
                    repo,
                    family,
                    subrepo,

                    name,
                    effname,

                    version,
                    origversion,
                    versionclass,

                    maintainers,
                    category,
                    comment,
                    homepage,
                    licenses,
                    downloads,

                    flags,
                    shadow,
                    verfixed,

                    flavors,

                    extrafields
                ) VALUES (
                    %s,
                    %s,
                    %s,

                    %s,
                    %s,

                    %s,
                    %s,
                    %s,

                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,

                    %s,
                    %s,
                    %s,

                    %s,

                    %s
                )
                """,
                [
                    (
                        package.repo,
                        package.family,
                        package.subrepo,

                        package.name,
                        package.effname,

                        package.version,
                        package.origversion,
                        package.versionclass,

                        package.maintainers,
                        package.category,
                        package.comment,
                        package.homepage,
                        package.licenses,
                        package.downloads,

                        package.flags,
                        package.shadow,
                        package.verfixed,

                        package.flavors,

                        json.dumps(package.extrafields),
                    ) for package in packages
                ]
            )

    def QueryMetapackages(self, request, limit=500):
        request.Limit(limit)

        query, args = request.GetQuery()

        return self.RequestManyAsPackages(
            """
            SELECT
                repo,
                family,
                subrepo,

                name,
                effname,

                version,
                origversion,
                versionclass,

                maintainers,
                category,
                comment,
                homepage,
                licenses,
                downloads,

                flags,
                shadow,
                verfixed,

                flavors,

                extrafields
            FROM packages
            WHERE effname IN (
                {}
            )
            """.format(query),
            *args
        )

    linkcheck_status_timeout = -1
    linkcheck_status_too_many_redirects = -2
    linkcheck_status_unknown_error = -3
    linkcheck_status_cannot_connect = -4
    linkcheck_status_invalid_url = -5
    linkcheck_status_dns_error = -6
