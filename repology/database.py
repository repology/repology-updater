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

import datetime

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

        self.effname_sorting = None
        self.limit = None

        # maintainer (maintainer_metapackages)
        self.maintainer = None
        self.maintainer_outdated = False

        # num families (metapackage_repocounts)
        self.morefamilies = None
        self.lessfamilies = None

        # repos (repo_metapackages)
        self.repos = None
        self.repos_outdated = False

        # not repos (repo_metapackages + having)
        self.repo_not = None

    def NameStarting(self, name):
        if self.namecond:
            raise RuntimeError('duplicate effname condition')
        self.namecond = '>='
        self.namebound = name
        self.nameorder = 'ASC'

    def NameAfter(self, name):
        if self.namecond:
            raise RuntimeError('duplicate effname condition')
        self.namecond = '>'
        self.namebound = name
        self.nameorder = 'ASC'

    def NameBefore(self, name):
        if self.namecond:
            raise RuntimeError('duplicate effname condition')
        self.namecond = '<'
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

    def OutdatedForMaintainer(self, maintainer):
        if self.maintainer:
            raise RuntimeError('duplicate maintainer condition')
        self.maintainer = maintainer
        self.maintainer_outdated = True

    def InRepo(self, repo):
        if self.repos and repo not in self.repos:
            raise RuntimeError('duplicate repository condition')

        self.repos = set((repo,))

    def InAnyRepo(self, repos):
        if self.repos:
            for currentrepo in self.repos:
                if currentrepo not in repos:
                    raise RuntimeError('duplicate repository condition')
        else:
            self.repos = set(repos)

    def OutdatedInRepo(self, repo):
        if self.repos and repo not in self.repos:
            raise RuntimeError('duplicate repository condition')

        self.repos = set((repo,))
        self.repos_outdated = True

    def NotInRepo(self, repo):
        if self.repo_not:
            raise RuntimeError('duplicate not-in-repository condition')
        self.repo_not = repo

    def MoreFamilies(self, num):
        if self.morefamilies:
            raise RuntimeError('duplicate more families condition')
        self.morefamilies = num

    def LessFamilies(self, num):
        if self.lessfamilies:
            raise RuntimeError('duplicate less families condition')
        self.lessfamilies = num

    def Limit(self, limit):
        if self.limit:
            raise RuntimeError('duplicate limit')
        self.limit = limit

    def GetQuery(self):
        tables = set()
        where = AndQuery()
        having = AndQuery()

        # table joins and conditions
        if self.maintainer:
            tables.add('maintainer_metapackages')
            if self.maintainer_outdated:
                where.Append('maintainer_metapackages.maintainer = %s AND maintainer_metapackages.num_packages_outdated > 0', self.maintainer)
            else:
                where.Append('maintainer_metapackages.maintainer = %s', self.maintainer)

        if self.morefamilies:
            tables.add('metapackage_repocounts')
            where.Append('metapackage_repocounts.num_families >= %s', self.morefamilies)

        if self.lessfamilies:
            tables.add('metapackage_repocounts')
            where.Append('metapackage_repocounts.num_families <= %s', self.lessfamilies)

        if self.repos:
            tables.add('repo_metapackages')
            if self.repos_outdated:
                where.Append('repo_metapackages.repo in (' + ','.join(['%s'] * len(self.repos)) + ') and repo_metapackages.num_outdated > 0', *self.repos)
            else:
                where.Append('repo_metapackages.repo in (' + ','.join(['%s'] * len(self.repos)) + ')', *self.repos)

        if self.repo_not:
            tables.add('repo_metapackages as repo_metapackages1')
            having.Append('count(nullif(repo_metapackages1.repo = %s, false)) = 0', self.repo_not)

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
    def __init__(self, dsn, readonly=True):
        self.db = psycopg2.connect(dsn)
        if readonly:
            self.db.set_session(readonly=True, autocommit=True)
        self.cursor = self.db.cursor()

    def CreateSchema(self):
        self.cursor.execute('DROP TABLE IF EXISTS packages CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS repositories CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS repositories_history CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS totals_history CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS links CASCADE')

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
                num_metapackages_unique integer not null default 0,
                num_metapackages_newest integer not null default 0,
                num_metapackages_outdated integer not null default 0,

                last_update timestamp with time zone
            )
        """)

        # repository_history
        self.cursor.execute("""
            CREATE TABLE repositories_history (
                ts timestamp with time zone not null primary key,
                statistics json not null
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

        self.cursor.execute("""
            CREATE INDEX ON maintainer_metapackages(effname)
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
                    count(DISTINCT family) AS num_families,
                    bool_and(shadow) AS shadow_only
                FROM packages
                GROUP BY effname
                ORDER BY effname
            WITH DATA
        """)

        self.cursor.execute('CREATE UNIQUE INDEX ON metapackage_repocounts(effname)')
        self.cursor.execute('CREATE INDEX ON metapackage_repocounts(num_repos)')
        self.cursor.execute('CREATE INDEX ON metapackage_repocounts(num_families)')
        self.cursor.execute('CREATE INDEX ON metapackage_repocounts(shadow_only, num_families)')

        # links for link checker
        self.cursor.execute("""
            CREATE TABLE links (
                url varchar(2048) not null primary key,
                last_extracted timestamp with time zone not null,
                last_checked timestamp with time zone,
                last_success timestamp with time zone,
                last_failure timestamp with time zone,
                status smallint,
                redirect smallint,
                size bigint,
                location varchar(2048)
            )
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
                num_metapackages_unique = 0,
                num_metapackages_newest = 0,
                num_metapackages_outdated = 0
        """)

    def AddPackages(self, packages):
        self.cursor.executemany(
            """
            INSERT INTO packages(
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
            )
            """,
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
        self.cursor.executemany(
            """
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
            [[name] for name in reponames]
        )

    def UpdateViews(self):
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY repo_metapackages""")
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainer_metapackages""")
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY maintainers""")
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY metapackage_repocounts""")

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
                    num_metapackages_unique,
                    num_metapackages_newest,
                    num_metapackages_outdated
                ) SELECT
                    repo,
                    count(*),
                    count(nullif(unique_only, false)),
                    count(nullif(NOT unique_only and num_packages_newest>0, false)),
                    count(nullif(NOT unique_only and num_packages_newest=0, false))
                FROM(
                        SELECT
                            repo,
                            TRUE as unique_only,
                            count(*) as num_packages,
                            count(nullif(versionclass=1, false)) as num_packages_newest
                        FROM packages
                        WHERE effname IN (
                            SELECT
                                effname
                            FROM metapackage_repocounts
                            WHERE NOT shadow_only AND num_families = 1
                        )
                        GROUP BY repo, effname
                    UNION ALL
                        SELECT
                            repo,
                            FALSE as unique_only,
                            count(*) as num_packages,
                            count(nullif(versionclass=1, false)) as num_packages_newest
                        FROM packages
                        WHERE effname IN (
                            SELECT
                                effname
                            FROM metapackage_repocounts
                            WHERE NOT shadow_only AND num_families > 1
                        )
                        GROUP BY repo, effname
                ) AS TEMP
                GROUP BY repo
                ON CONFLICT (name)
                DO UPDATE SET
                    num_metapackages = EXCLUDED.num_metapackages,
                    num_metapackages_unique = EXCLUDED.num_metapackages_unique,
                    num_metapackages_newest = EXCLUDED.num_metapackages_newest,
                    num_metapackages_outdated = EXCLUDED.num_metapackages_outdated
        """)

    def Commit(self):
        self.db.commit()

    def GetMetapackage(self, name):
        self.cursor.execute(
            """
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
        req = MetapackageRequest()

        for f in filters:
            if f:
                f.ApplyToRequest(req)

        req.Limit(limit)

        query, args = req.GetQuery()

        self.cursor.execute(
            """
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
            )
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
        self.cursor.execute("""SELECT count(*) FROM metapackage_repocounts WHERE NOT shadow_only""")

        return self.cursor.fetchall()[0][0]

    def GetMaintainersCount(self):
        self.cursor.execute("""SELECT count(*) FROM maintainers""")

        return self.cursor.fetchall()[0][0]

    def GetMaintainers(self, offset=0, limit=500):
        self.cursor.execute(
            """
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
            request += ' WHERE maintainer < \'a\''
        elif letter >= 'z':
            request += ' WHERE maintainer >= \'z\''
        else:
            request += ' WHERE maintainer >= %s'
            request += ' AND maintainer < %s'
            args += [letter, chr(ord(letter) + 1)]

        request += ' ORDER BY maintainer'

        self.cursor.execute(request, args)

        return [
            {
                'maintainer': row[0],
                'num_packages': row[1],
                'num_packages_outdated': row[2]
            } for row in self.cursor.fetchall()
        ]

    def GetMaintainerInformation(self, maintainer):
        self.cursor.execute(
            """
            SELECT
                num_packages,
                num_packages_newest,
                num_packages_outdated,
                num_packages_ignored,
                num_metapackages
            FROM maintainers
            WHERE maintainer = %s
            """,
            (maintainer,)
        )

        rows = self.cursor.fetchall()

        if not rows:
            return None

        return {
            'num_packages': rows[0][0],
            'num_packages_newest': rows[0][1],
            'num_packages_outdated': rows[0][2],
            'num_packages_ignored': rows[0][3],
            'num_metapackages': rows[0][4],
        }

    def GetMaintainerMetapackages(self, maintainer, limit=1000):
        self.cursor.execute(
            """
            SELECT
                effname
            FROM maintainer_metapackages
            WHERE maintainer = %s
            ORDER BY effname
            LIMIT %s
            """,
            (maintainer, limit)
        )

        return [row[0] for row in self.cursor.fetchall()]

    def GetMaintainerSimilarMaintainers(self, maintainer, limit=100):
        # this obscure request needs some clarification
        #
        # what we calculate as score here is actually Jaccard index
        # (see wikipedia) for two sets (of metapackages maintained by
        # two maintainers)
        #
        # let M = set of metapackages for maintainer passed to this function
        # let C = set of metapackages for other maintainer we test for similarity
        #
        # score = |M⋂C| / |M⋃C| = |M⋂C| / (|M| + |C| - |M⋂C|)
        #
        # - count(*) is number of common metapackages for both maintainers, e.g. |M⋂C|
        # - min(num_metapackages) is number of metapackages for candidate maintainer |C|
        #   we use min because we use GROUP BY and just need a group operation; since we
        #   group by maintainer and join by maintainer, num_metapackages is the same
        #   in all records, and we may pick min, max, avg, whatever
        # - sub-select just gets |M|
        # - the divisor is |M⋃C| = |M| + |C| - |M⋂C|
        self.cursor.execute(
            """
            SELECT
                maintainer,
                count(*) AS count,
                100.0 * count(*) / (
                    min(num_metapackages) -
                    count(*) +
                    (
                        SELECT num_metapackages
                        FROM maintainers
                        WHERE maintainer=%s
                    )
                ) AS score
            FROM maintainer_metapackages
            INNER JOIN maintainers USING(maintainer)
            WHERE
                maintainer != %s AND
                effname IN (
                    SELECT
                        effname
                    FROM maintainer_metapackages
                    WHERE maintainer=%s
                )
            GROUP BY maintainer
            ORDER BY score DESC
            LIMIT %s
            """,
            (maintainer, maintainer, maintainer, limit)
        )

        return [
            {
                'maintainer': row[0],
                'count': row[1],
                'match': row[2],
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
                num_metapackages_unique,
                num_metapackages_newest,
                num_metapackages_outdated,
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
                'num_metapackages_unique': row[6],
                'num_metapackages_newest': row[7],
                'num_metapackages_outdated': row[8],
                'last_update_utc': row[9],
                'since_last_update': row[10]
            } for row in self.cursor.fetchall()
        ]

    def GetRepositoriesHistoryAgo(self, seconds=60 * 60 * 24):
        self.cursor.execute("""
            SELECT
                ts,
                now() - ts,
                json_array_elements(statistics)
            FROM repositories_history
            WHERE ts IN (
                SELECT
                    ts
                FROM repositories_history
                WHERE ts < now() - INTERVAL %s
                ORDER BY ts DESC
                LIMIT 1
            );
        """, (datetime.timedelta(seconds=seconds),)
        )

        return [
            {
                'timestamp': row[0],
                'timedelta': row[1],
                **row[2]
            }
            for row in self.cursor.fetchall()
        ]

    def GetRepositoriesHistoryPeriod(self, seconds=60 * 60 * 24, repo=None):
        self.cursor.execute("""
            SELECT
                ts,
                now() - ts,
                statistics
            FROM repositories_history
            WHERE ts >= now() - INTERVAL %s
            ORDER BY ts
        """, (datetime.timedelta(seconds=seconds),)
        )

        return [
            {
                'timestamp': row[0],
                'timedelta': row[1],
                'statistics': row[2]
            }
            for row in self.cursor.fetchall()
        ]

    def Query(self, query, *args):
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def SnapshotRepositoriesHistory(self):
        self.cursor.execute(
            """
            INSERT
            INTO repositories_history(
                ts,
                statistics
            )
            SELECT
                now(),
                array_to_json(array_agg(row_to_json(statistics_snapshot)))
            FROM (
                SELECT
                    name,
                    num_metapackages,
                    num_metapackages_unique,
                    num_metapackages_newest,
                    num_metapackages_outdated
                FROM repositories
            ) AS statistics_snapshot
           """
        )

    def ExtractLinks(self):
        self.cursor.execute(
            """
            INSERT
            INTO links(
                url,
                last_extracted
            ) SELECT
                unnest(downloads),
                now()
            FROM packages
            UNION
            SELECT
                homepage,
                now()
            FROM packages
            WHERE homepage IS NOT NULL AND homepage LIKE 'http%%' AND repo NOT IN('cpan', 'pypi', 'rubygems', 'hackage')
            ON CONFLICT (url)
            DO UPDATE SET
                last_extracted = now()
            """
        )

    def GetLinksForCheck(self, after=None, prefix=None, recheck_age=None, limit=None, unchecked_only=False, checked_only=False, failed_only=False, succeeded_only=False):
        conditions = []
        args = []

        # reduce the noise while linkchecker code doesn't support other schemas
        conditions.append('(url LIKE %s OR url LIKE %s)')
        args.append('http://%')
        args.append('https://%')

        if after is not None:
            conditions.append('url > %s')
            args.append(after)

        if prefix is not None:
            conditions.append('url LIKE %s')
            args.append(prefix + '%')

        if recheck_age is not None:
            conditions.append('(last_checked IS NULL OR last_checked <= now() - INTERVAL %s)')
            args.append(datetime.timedelta(seconds=recheck_age))

        if unchecked_only:
            conditions.append('last_checked IS NULL')

        if checked_only:
            conditions.append('last_checked IS NOT NULL')

        if failed_only:
            conditions.append('status != 200')

        if succeeded_only:
            conditions.append('status == 200')

        conditions_expr = ''
        limit_expr = ''

        if conditions:
            conditions_expr = 'WHERE ' + ' AND '.join(conditions)

        if limit:
            limit_expr = 'LIMIT %s'
            args.append(limit)

        self.cursor.execute(
            """
            SELECT
                url
            FROM links
            {}
            ORDER BY url
            {}
            """.format(conditions_expr, limit_expr),
            args
        )

        return [row[0] for row in self.cursor.fetchall()]

    linkcheck_status_timeout = -1
    linkcheck_status_too_many_redirects = -2
    linkcheck_status_unknown_error = -3
    linkcheck_status_cannot_connect = -4
    linkcheck_status_invalid_url = -5

    def UpdateLinkStatus(self, url, status, redirect=None, size=None, location=None):
        success = status == 200

        self.cursor.execute(
            """
            UPDATE links
            SET
                last_checked = now(),
                last_success = CASE WHEN %s THEN now() ELSE last_success END,
                last_failure = CASE WHEN %s THEN now() ELSE last_failure END,
                status = %s,
                redirect = %s,
                size = %s,
                location = %s
            WHERE url = %s
            """,
            (
                success,
                not success,
                status,
                redirect,
                size,
                location,
                url
            )
        )

    def GetMetapackageLinkStatuses(self, name):
        self.cursor.execute(
            """
            SELECT
                url,
                last_checked,
                last_success,
                last_failure,
                status,
                redirect,
                size,
                location
            FROM links
            WHERE url in (
                SELECT
                    unnest(downloads) as url
                FROM packages
                WHERE effname = %s
                UNION
                SELECT
                    homepage
                FROM packages
                WHERE homepage IS NOT NULL and effname = %s
            )
            """,
            (name, name)
        )

        return {
            row[0]: {
                'last_checked': row[1],
                'last_success': row[2],
                'last_failure': row[3],
                'status': row[4],
                'redirect': row[5],
                'size': row[6],
                'location': row[7]
            }
            for row in self.cursor.fetchall()
        }
