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

import psycopg2
import sys

from repology.package import Package


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
        return 'metapackages'

    def GetWhere(self):
        return 'effname >= %s' if self.name else 'true'

    def GetWhereArgs(self):
        return [ self.name ] if self.name else []

    def GetSort(self):
        return 'effname ASC'


class NameAfterQueryFilter(QueryFilter):
    def __init__(self, name=None):
        self.name = name

    def GetTable(self):
        return 'metapackages'

    def GetWhere(self):
        return 'effname > %s' if self.name else 'true'

    def GetWhereArgs(self):
        return [ self.name ] if self.name else []

    def GetSort(self):
        return 'effname ASC'


class NameBeforeQueryFilter(QueryFilter):
    def __init__(self, name=None):
        self.name = name

    def GetTable(self):
        return 'metapackages'

    def GetWhere(self):
        return 'effname < %s' if self.name else 'true'

    def GetWhereArgs(self):
        return [ self.name ] if self.name else []

    def GetSort(self):
        return 'effname DESC'


class NameSubstringQueryFilter(QueryFilter):
    def __init__(self, name):
        self.name = name

    def GetTable(self):
        return 'metapackages'

    def GetWhere(self):
        return '{table}.effname like %s'

    def GetWhereArgs(self):
        return [ self.name + "%" ]


class MaintainerQueryFilter(QueryFilter):
    def __init__(self, maintainer):
        self.maintainer = maintainer

    def GetTable(self):
        return 'maintainers'

    def GetWhere(self):
        return '{table}.maintainer=%s'

    def GetWhereArgs(self):
        return [ self.maintainer ]


class InRepoQueryFilter(QueryFilter):
    def __init__(self, repo):
        self.repo = repo

    def GetTable(self):
        return 'metapackages'

    def GetWhere(self):
        return '{table}.repo=%s'

    def GetWhereArgs(self):
        return [ self.repo ]


class InAnyRepoQueryFilter(QueryFilter):
    def __init__(self, repos):
        self.repos = repos

    def GetTable(self):
        return 'metapackages'

    def GetWhere(self):
        return '{table}.repo in (' + ','.join(['%s'] * len(self.repos)) + ')'

    def GetWhereArgs(self):
        return [ repo for repo in self.repos ]


class OutdatedInRepoQueryFilter(QueryFilter):
    def __init__(self, repo):
        self.repo = repo

    def GetTable(self):
        return 'metapackages'

    def GetWhere(self):
        return '{table}.repo=%s AND {table}.num_outdated>0'

    def GetWhereArgs(self):
        return [ self.repo ]


class NotInRepoQueryFilter(QueryFilter):
    def __init__(self, repo):
        self.repo = repo

    def GetTable(self):
        return 'metapackages'

    def GetHaving(self):
        return 'count(nullif({table}.repo = %s, false)) = 0'

    def GetHavingArgs(self):
        return [ self.repo ]


class MetapackageQueryConstructor:
    def __init__(self, *filters, limit=500):
        self.filters = filters
        self.limit = limit

    def GetQuery(self):
        tables = []
        where = []
        where_args = []
        having = []
        having_args = []
        args = []
        sort = None

        tablenum = 0
        for f in self.filters:
            tableid = '{}{}'.format(f.GetTable(), str(tablenum))

            tables.append('{} AS {}'.format(f.GetTable(), tableid))

            if f.GetWhere():
                where.append(f.GetWhere().format(table=tableid))
                where_args += f.GetWhereArgs()

            if f.GetHaving():
                having.append(f.GetHaving().format(table=tableid))
                having_args += f.GetHavingArgs()

            if f.GetSort():
                if sort is None:
                    sort = f.GetSort()
                elif sort == f.GetSort():
                    pass
                else:
                    raise RuntimeError("sorting mode conflict in query")

            tablenum += 1

        query = 'SELECT DISTINCT effname FROM '

        query += tables[0]
        for table in tables[1:]:
            query += ' INNER JOIN {} USING(effname)'.format(table)

        if where:
            query += ' WHERE '
            query += ' AND '.join(where)
            args += where_args

        if having:
            query += ' GROUP BY effname HAVING ' + ' AND '.join(having)
            args += having_args

        if sort:
            query += ' ORDER BY ' + sort
        else:
            query += ' ORDER BY effname ASC'

        query += ' LIMIT %s'
        args.append(self.limit)

        return (query, args)


class Database:
    def __init__(self, dsn, readonly=True):
        self.db = psycopg2.connect(dsn)
        if readonly:
            self.db.set_session(readonly=True, autocommit=True)
        self.cursor = self.db.cursor()

    def CreateSchema(self):
        self.cursor.execute("""
            DROP TABLE IF EXISTS packages CASCADE
        """)

        self.cursor.execute("""
            CREATE TABLE packages (
                repo varchar(255) not null,
                family varchar(255) not null,

                name varchar(255) not null,
                effname varchar(255) not null,

                version varchar(255) not null,
                origversion varchar(255),
                effversion varchar(255),
                versionclass smallint,

                maintainers varchar(1024)[],
                category varchar(255),
                comment text,
                homepage varchar(1024),
                licenses varchar(1024)[],
                downloads varchar(1024)[],

                ignorepackage bool not null,
                shadow bool not null,
                ignoreversion bool not null
            )
        """)

        self.cursor.execute("""
            CREATE INDEX ON packages(effname)
        """)

        # metapackages
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW metapackages
                AS
                    SELECT
                        repo,
                        effname,
                        count(nullif(versionclass=1, false)) AS num_newest,
                        count(nullif(versionclass=2, false)) AS num_outdated,
                        count(nullif(versionclass=3, false)) AS num_ignored
                    FROM packages
                    WHERE effname IN (
                        SELECT
                            effname
                        FROM packages
                        GROUP BY effname
                        HAVING count(nullif(shadow, true)) > 0
                    )
                    GROUP BY effname,repo
                WITH DATA
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON metapackages(repo, effname)
        """)

        self.cursor.execute("""
            CREATE INDEX ON metapackages(effname)
        """)

        # maintainers
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW maintainers
                AS
                    SELECT
                        unnest(maintainers) as maintainer,
                        effname
                    FROM packages
                    GROUP BY maintainer, effname
                WITH DATA
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON maintainers(maintainer, effname)
        """)

        # not used yet
        #self.cursor.execute("""
        #    CREATE MATERIALIZED VIEW maintainer_package_counts AS
        #        SELECT
        #            unnest(maintainers) AS maintainer,
        #            count(1) AS num_packages,
        #            count(DISTINCT effname) AS num_metapackages,
        #            count(nullif(versionclass = 1, false)) AS num_newest,
        #            count(nullif(versionclass = 2, false)) AS num_outdated,
        #            count(nullif(versionclass = 3, false)) AS num_ignored
        #        FROM packages
        #        GROUP BY maintainer
        #        ORDER BY maintainer
        #    WITH DATA
        #""")

        #self.cursor.execute("""
        #    CREATE UNIQUE INDEX ON maintainer_package_counts(maintainer)
        #""")

    def Clear(self):
        self.cursor.execute("""DELETE FROM packages""")

    def AddPackages(self, packages):
        self.cursor.executemany("""INSERT INTO packages(
            repo,
            family,

            name,
            effname,

            version,
            origversion,
            effversion,
            versionclass,

            maintainers,
            category,
            comment,
            homepage,
            licenses,
            downloads,

            ignorepackage,
            shadow,
            ignoreversion
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
            %s
        )""",
            [
                (
                    package.repo,
                    package.family,

                    package.name,
                    package.effname,

                    package.version,
                    package.origversion,
                    package.effversion,
                    package.versionclass,

                    package.maintainers,
                    package.category,
                    package.comment,
                    package.homepage,
                    package.licenses,
                    package.downloads,

                    package.ignore,
                    package.shadow,
                    package.ignoreversion,
                ) for package in packages
            ]
        )

    def UpdateViews(self):
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY metapackages""");
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainers""");
        #self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainer_package_counts""");

    def Commit(self):
        self.db.commit()

    def GetMetapackage(self, name):
        self.cursor.execute("""
            SELECT
                repo,
                family,

                name,
                effname,

                version,
                origversion,
                effversion,
                versionclass,

                maintainers,
                category,
                comment,
                homepage,
                licenses,
                downloads,

                ignorepackage,
                shadow,
                ignoreversion
            FROM packages
            WHERE effname = %s
        """,
            (name,)
        )

        return [
            Package(
                repo=row[0],
                family=row[1],

                name=row[2],
                effname=row[3],

                version=row[4],
                origversion=row[5],
                effversion=row[6],
                versionclass=row[7],

                maintainers=row[8],
                category=row[9],
                comment=row[10],
                homepage=row[11],
                licenses=row[12],
                downloads=row[13],

                ignore=row[14],
                shadow=row[15],
                ignoreversion=row[16],
            ) for row in self.cursor.fetchall()
        ]

    def GetMetapackages(self, *filters, limit=500):
        query, args = MetapackageQueryConstructor(*filters, limit=limit).GetQuery()

        self.cursor.execute("""
            SELECT
                repo,
                family,

                name,
                effname,

                version,
                origversion,
                effversion,
                versionclass,

                maintainers,
                category,
                comment,
                homepage,
                licenses,
                downloads,

                ignorepackage,
                shadow,
                ignoreversion
            FROM packages WHERE effname IN (
                {}
            ) ORDER BY effname
        """.format(query),
            args
        )

        return [
            Package(
                repo=row[0],
                family=row[1],

                name=row[2],
                effname=row[3],

                version=row[4],
                origversion=row[5],
                effversion=row[6],
                versionclass=row[7],

                maintainers=row[8],
                category=row[9],
                comment=row[10],
                homepage=row[11],
                licenses=row[12],
                downloads=row[13],

                ignore=row[14],
                shadow=row[15],
                ignoreversion=row[16],
            ) for row in self.cursor.fetchall()
        ]
