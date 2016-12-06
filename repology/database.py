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
            CREATE UNIQUE INDEX ON maintainer_package_counts(maintainer)
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

    def Commit(self):
        self.db.commit()

    def GetNumPackages(self):
        self.cursor.execute("""SELECT count(*) FROM packages""");
        return self.cursor.fetchone()[0]

    def GetNumMetapackages(self):
        self.cursor.execute("""SELECT count(*) FROM (SELECT DISTINCT effname FROM packages) AS temp""");
        return self.cursor.fetchone()[0]
