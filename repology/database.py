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
        self.cursor.execute("""drop table if exists packages cascade""")

        self.cursor.execute("""create table packages (
            id serial not null primary key,

            repo varchar(255) not null,
            family varchar(255) not null,

            name varchar(255) not null,
            effname varchar(255) not null,

            version varchar(255) not null,
            origversion varchar(255),
            effversion varchar(255),
            versionclass smallint,

            maintainers varchar(1024),
            category varchar(255),
            comment varchar(2048),
            homepage varchar(1024),
            licenses varchar(1024),
            downloads varchar(1024),

            ignorepackage bool not null,
            shadow bool not null,
            ignoreversion bool not null
        )""")

        self.cursor.execute("""create index on packages(effname)""")

    def Clear(self):
        self.cursor.execute("""delete from packages""")

    def AddPackages(self, packages):
        self.cursor.executemany("""insert into packages(
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
        ) values (
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

                    ' '.join(package.maintainers),
                    package.category,
                    package.comment,
                    package.homepage,
                    ' '.join(package.licenses),
                    ' '.join(package.downloads),

                    package.ignore,
                    package.shadow,
                    package.ignoreversion,
                ) for package in packages
            ]
        )

    def Commit(self):
        self.db.commit()

    def GetNumPackages(self):
        self.cursor.execute("""select count(*) from packages""");
        return self.cursor.fetchone()[0]

    def GetNumMetapackages(self):
        self.cursor.execute("""select count(*) from (select distinct effname from packages) as temp""");
        return self.cursor.fetchone()[0]
