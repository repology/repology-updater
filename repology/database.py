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
            if f is None:
                continue

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

        if self.limit:
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
            DROP TABLE IF EXISTS repositories CASCADE
        """)

        self.cursor.execute("""
            DROP TABLE IF EXISTS families CASCADE
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

        # repositories
        self.cursor.execute("""
            CREATE TABLE repositories (
                name varchar(255) not null primary key,

                num_packages integer not null default 0,
                num_packages_newest integer not null default 0,
                num_packages_outdated integer not null default 0,
                num_packages_ignored integer not null default 0,

                num_metapackages integer not null default 0,
                num_metapackages_newest integer not null default 0,

                last_update timestamp with time zone
            )
        """)

        self.cursor.execute("""
            CREATE TABLE families (
                name varchar(255) not null primary key,

                num_metapackages integer not null default 0,
                num_metapackages_newest integer not null default 0
            )
        """)

        # repo_metapackages
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW repo_metapackages
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
            CREATE UNIQUE INDEX ON repo_metapackages(repo, effname)
        """)

        self.cursor.execute("""
            CREATE INDEX ON repo_metapackages(effname)
        """)

        # maintainer_metapackages
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW maintainer_metapackages
                AS
                    SELECT
                        unnest(maintainers) as maintainer,
                        effname,
                        count(1) AS num_packages,
                        count(nullif(versionclass = 1, false)) AS num_packages_newest,
                        count(nullif(versionclass = 2, false)) AS num_packages_outdated,
                        count(nullif(versionclass = 3, false)) AS num_packages_ignored
                    FROM packages
                    GROUP BY maintainer, effname
                WITH DATA
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON maintainer_metapackages(maintainer, effname)
        """)

        # maintainers
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW maintainers AS
                SELECT
                    unnest(maintainers) AS maintainer,
                    count(1) AS num_packages,
                    count(DISTINCT effname) AS num_metapackages,
                    count(nullif(versionclass = 1, false)) AS num_packages_newest,
                    count(nullif(versionclass = 2, false)) AS num_packages_outdated,
                    count(nullif(versionclass = 3, false)) AS num_packages_ignored
                FROM packages
                GROUP BY maintainer
                ORDER BY maintainer
            WITH DATA
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON maintainers(maintainer)
        """)

        # repo counts
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW metapackage_repocounts AS
                SELECT
                    effname,
                    count(DISTINCT repo) AS num_repos,
                    count(DISTINCT family) AS num_families
                FROM packages
                GROUP BY effname
                ORDER BY effname
            WITH DATA
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON metapackage_repocounts(effname)
        """)

        self.cursor.execute("""
            CREATE INDEX ON metapackage_repocounts(num_repos)
        """)

        self.cursor.execute("""
            CREATE INDEX ON metapackage_repocounts(num_families)
        """)

    def Clear(self):
        self.cursor.execute("""DELETE FROM packages""")
        self.cursor.execute("""
            UPDATE repositories
            SET
                num_packages = 0,
                num_packages_newest = 0,
                num_packages_outdated = 0,
                num_packages_ignored = 0,
                num_metapackages = 0,
                num_metapackages_newest = 0
        """)
        self.cursor.execute("""
            UPDATE families
            SET
                num_metapackages = 0,
                num_metapackages_newest = 0
        """)

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

    def MarkRepositoriesUpdated(self, reponames):
        self.cursor.executemany("""
            INSERT
                INTO repositories (
                    name,
                    last_update
                ) VALUES (
                    %s,
                    now()
                )
                ON CONFLICT (name)
                DO UPDATE SET
                    last_update = now()
        """,
            [ [ name ] for name in reponames ]
        )

    def UpdateViews(self):
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY repo_metapackages""");
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainer_metapackages""");
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainers""");
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY metapackage_repocounts""");

        # package stats
        self.cursor.execute("""
            INSERT
                INTO repositories (
                    name,
                    num_packages,
                    num_packages_newest,
                    num_packages_outdated,
                    num_packages_ignored
                ) SELECT
                    repo,
                    sum(num_packages),
                    sum(num_packages_newest),
                    sum(num_packages_outdated),
                    sum(num_packages_ignored)
                FROM(
                    SELECT
                        repo,
                        count(*) as num_packages,
                        count(nullif(versionclass=1, false)) as num_packages_newest,
                        count(nullif(versionclass=2, false)) as num_packages_outdated,
                        count(nullif(versionclass=3, false)) as num_packages_ignored
                    FROM packages
                    GROUP BY repo, effname
                ) AS TEMP
                GROUP BY repo
                ON CONFLICT (name)
                DO UPDATE SET
                    num_packages = EXCLUDED.num_packages,
                    num_packages_newest = EXCLUDED.num_packages_newest,
                    num_packages_outdated = EXCLUDED.num_packages_outdated,
                    num_packages_ignored = EXCLUDED.num_packages_ignored
        """)

        # metapackage stats
        self.cursor.execute("""
            INSERT
                INTO repositories (
                    name,
                    num_metapackages,
                    num_metapackages_newest
                ) SELECT
                    repo,
                    count(*),
                    count(nullif(num_packages_newest>0, false))
                FROM(
                    SELECT
                        repo,
                        count(*) as num_packages,
                        count(nullif(versionclass=1, false)) as num_packages_newest
                    FROM packages
                    WHERE effname IN (
                        SELECT
                            DISTINCT effname
                            FROM PACKAGES
                        WHERE NOT shadow
                    )
                    GROUP BY repo, effname
                ) AS TEMP
                GROUP BY repo
                ON CONFLICT (name)
                DO UPDATE SET
                    num_metapackages = EXCLUDED.num_metapackages,
                    num_metapackages_newest = EXCLUDED.num_metapackages_newest
        """)

        self.cursor.execute("""
            INSERT
                INTO families (
                    name,
                    num_metapackages,
                    num_metapackages_newest
                ) SELECT
                    family,
                    count(*),
                    count(nullif(num_packages_newest>0, false))
                FROM(
                    SELECT
                        family,
                        count(*) as num_packages,
                        count(nullif(versionclass=1, false)) as num_packages_newest
                    FROM packages
                    WHERE effname IN (
                        SELECT
                            DISTINCT effname
                            FROM PACKAGES
                        WHERE NOT shadow
                    )
                    GROUP BY family, effname
                ) AS TEMP
                GROUP BY family
                ON CONFLICT (name)
                DO UPDATE SET
                    num_metapackages = EXCLUDED.num_metapackages,
                    num_metapackages_newest = EXCLUDED.num_metapackages_newest
        """)

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

    def GetPackagesCount(self):
        self.cursor.execute("""SELECT count(*) FROM packages""")

        return self.cursor.fetchall()[0][0]

    def GetMetapackagesCount(self):
        self.cursor.execute("""SELECT count(*) FROM metapackage_repocounts""")

        return self.cursor.fetchall()[0][0]

    def GetMaintainersCount(self):
        self.cursor.execute("""SELECT count(*) FROM maintainers""")

        return self.cursor.fetchall()[0][0]

    def GetMaintainers(self, offset=0, limit=500):
        self.cursor.execute("""
            SELECT
                maintainer,
                num_packages,
                num_metapackages
            FROM maintainers
            ORDER BY maintainer
            LIMIT %s
            OFFSET %s
        """,
            (limit, offset,)
        )

        return [
            {
                'maintainer': row[0],
                'num_packages': row[1],
                'num_metapackages': row[2]
            } for row in self.cursor.fetchall()
        ]

    def GetMaintainersByLetter(self, letter=None):
        request = """
            SELECT
                maintainer,
                num_packages,
                num_packages_outdated
            FROM maintainers
        """

        args = []
        if letter:
            letter = letter.lower()[0]
        if not letter or letter < 'a':
            request += " WHERE maintainer < 'a'"
        elif letter >= 'z':
            request += " WHERE maintainer >= 'z'"
        else:
            request += " WHERE maintainer >= %s"
            request += " AND maintainer < %s"
            args += [ letter, chr(ord(letter) + 1) ]

        request += " ORDER BY maintainer"

        self.cursor.execute(request, args)

        return [
            {
                'maintainer': row[0],
                'num_packages': row[1],
                'num_packages_outdated': row[2]
            } for row in self.cursor.fetchall()
        ]

    def GetRepositories(self):
        self.cursor.execute("""
            SELECT
                name,
                num_packages,
                num_packages_newest,
                num_packages_outdated,
                num_packages_ignored,
                num_metapackages,
                num_metapackages_newest,
                last_update at time zone 'UTC',
                now() - last_update
            FROM repositories
        """)

        return [
            {
                'name': row[0],
                'num_packages': row[1],
                'num_packages_newest': row[2],
                'num_packages_outdated': row[3],
                'num_packages_ignored': row[4],
                'num_metapackages': row[5],
                'num_metapackages_newest': row[6],
                'last_update_utc': row[7],
                'since_last_update': row[8]
            } for row in self.cursor.fetchall()
        ]

    def GetFamilies(self):
        self.cursor.execute("""
            SELECT
                name,
                num_metapackages,
                num_metapackages_newest
            FROM families
        """)

        return [
            {
                'name': row[0],
                'num_metapackages': row[1],
                'num_metapackages_newest': row[2],
            } for row in self.cursor.fetchall()
        ]

    def Query(self, query, *args):
        self.cursor.execute(query, args)
        return self.cursor.fetchall()
