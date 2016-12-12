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


class Database:
    def __init__(self, dsn):
        self.db = psycopg2.connect(dsn)
        self.cursor = self.db.cursor()

    def CreateSchema(self):
        self.cursor.execute("""
            DROP TABLE IF EXISTS packages CASCADE
        """)

        self.cursor.execute("""
            CREATE TABLE packages (
                id serial not null primary key,

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

        self.cursor.execute("""
            CREATE MATERIALIZED VIEW maintainer_package_counts AS
                SELECT
                    unnest(maintainers) AS maintainer,
                    count(1) AS num_packages,
                    count(DISTINCT effname) AS num_metapackages,
                    count(nullif(versionclass = 1, false)) AS num_newest,
                    count(nullif(versionclass = 2, false)) AS num_outdated,
                    count(nullif(versionclass = 3, false)) AS num_ignored
                FROM packages
                GROUP BY maintainer
                ORDER BY maintainer
            WITH DATA
        """)

        self.cursor.execute("""
            CREATE MATERIALIZED VIEW metapackages AS
                SELECT
                    effname as name,
                    count(nullif(shadow, true)) = 0 as shadow_only
                FROM packages
                GROUP BY effname
                ORDER BY effname
            WITH DATA
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON maintainer_package_counts(maintainer)
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX ON metapackages(name)
        """)

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
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainer_package_counts""");
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY metapackages""");

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

    def GetMetapackages(self, starting=None, after=None, before=None, limit=500):
        addendum = 'WHERE not shadow_only'
        args = []
        if starting is not None:
            addendum += " AND name >= %s ORDER BY name"
            args.append(starting)
        elif after is not None:
            addendum += " AND name > %s ORDER BY name"
            args.append(after)
        elif before is not None:
            addendum += " AND name < %s ORDER BY name DESC"
            args.append(before)
        else:
            addendum += " ORDER BY name"

        addendum += " LIMIT %s"
        args.append(limit)

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
                SELECT
                    name
                FROM metapackages
                {}
            ) ORDER BY effname
        """.format(addendum),
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
