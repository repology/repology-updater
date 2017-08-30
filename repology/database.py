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

import datetime
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
                where.Append('maintainer_metapackages.maintainer = %s AND maintainer_metapackages.num_packages_outdated > 0 AND maintainer_metapackages.num_packages_newest = 0', self.maintainer)
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
                where.Append('repo_metapackages.repo in (' + ','.join(['%s'] * len(self.repos)) + ') AND repo_metapackages.num_outdated > 0 AND repo_metapackages.num_newest = 0', *self.repos)
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
    def __init__(self, dsn, readonly=True, autocommit=False):
        self.db = psycopg2.connect(dsn)
        self.db.set_session(readonly=readonly, autocommit=autocommit)
        self.cursor = self.db.cursor()

    def CreateSchema(self):
        self.cursor.execute('DROP TABLE IF EXISTS packages CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS repositories CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS repositories_history CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS statistics CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS statistics_history CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS totals_history CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS links CASCADE')
        self.cursor.execute('DROP TABLE IF EXISTS problems CASCADE')

        self.cursor.execute("""
            CREATE TABLE packages (
                repo text not null,
                family text not null,
                subrepo text,

                name text not null,
                effname text not null,

                version text not null,
                origversion text,
                effversion text,
                versionclass smallint,

                maintainers text[],
                category text,
                comment text,
                homepage text,
                licenses text[],
                downloads text[],

                ignorepackage bool not null,
                shadow bool not null,
                ignoreversion bool not null,

                extrafields jsonb not null
            )
        """)

        self.cursor.execute("""
            CREATE INDEX ON packages(effname)
        """)

        # repositories
        self.cursor.execute("""
            CREATE TABLE repositories (
                name text not null primary key,

                num_packages integer not null default 0,
                num_packages_newest integer not null default 0,
                num_packages_outdated integer not null default 0,
                num_packages_ignored integer not null default 0,

                num_metapackages integer not null default 0,
                num_metapackages_unique integer not null default 0,
                num_metapackages_newest integer not null default 0,
                num_metapackages_outdated integer not null default 0,

                last_update timestamp with time zone,

                num_problems integer not null default 0,
                num_maintainers integer not null default 0
            )
        """)

        # repository_history
        self.cursor.execute("""
            CREATE TABLE repositories_history (
                ts timestamp with time zone not null primary key,
                snapshot jsonb not null
            )
        """)

        # statistics
        self.cursor.execute("""
            CREATE TABLE statistics (
                num_packages integer not null default 0,
                num_metapackages integer not null default 0,
                num_problems integer not null default 0,
                num_maintainers integer not null default 0
            )
        """)

        self.cursor.execute("""
            INSERT INTO statistics VALUES(DEFAULT)
        """)

        # statistics_history
        self.cursor.execute("""
            CREATE TABLE statistics_history (
                ts timestamp with time zone not null primary key,
                snapshot jsonb not null
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

        self.cursor.execute("""
            CREATE INDEX repo_metapackages_effname_trgm ON repo_metapackages USING gin (effname gin_trgm_ops);
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
                url text not null primary key,
                first_extracted timestamp with time zone not null,
                last_extracted timestamp with time zone not null,
                last_checked timestamp with time zone,
                last_success timestamp with time zone,
                last_failure timestamp with time zone,
                status smallint,
                redirect smallint,
                size bigint,
                location text
            )
        """)

        # problems
        self.cursor.execute("""
            CREATE TABLE problems (
                repo text not null,
                name text not null,
                effname text not null,
                maintainer text,
                problem text not null
            )
        """)

        self.cursor.execute('CREATE INDEX ON problems(effname)')
        self.cursor.execute('CREATE INDEX ON problems(repo, effname)')
        self.cursor.execute('CREATE INDEX ON problems(maintainer)')

        # reports
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id serial not null primary key,
                created timestamp with time zone not null,
                effname text not null,
                need_verignore boolean not null,
                need_split boolean not null,
                need_merge boolean not null,
                comment text,
                reply text,
                accepted boolean
            )
        """)

        self.cursor.execute('CREATE INDEX ON reports(effname)')

        # url_relations
        self.cursor.execute("""
            CREATE MATERIALIZED VIEW url_relations AS
                SELECT DISTINCT
                    effname,
                    regexp_replace(regexp_replace(homepage, '/?([#?].*)?$', ''), '^https?://(www\\.)?', '') as url
                FROM packages
                WHERE homepage ~ '^https?://'
            WITH DATA
        """)

        self.cursor.execute('CREATE UNIQUE INDEX ON url_relations(effname, url)')  # we only need url here because we need unique index for concurrent refresh
        self.cursor.execute('CREATE INDEX ON url_relations(url)')

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
                num_metapackages_outdated = 0,
                num_problems = 0,
                num_maintainers = 0
        """)
        self.cursor.execute("""DELETE FROM problems""")
        self.cursor.execute("""
            UPDATE statistics
            SET
                num_packages = 0,
                num_metapackages = 0,
                num_problems = 0,
                num_maintainers = 0
        """)

    def AddPackages(self, packages):
        self.cursor.executemany(
            """
            INSERT INTO packages(
                repo,
                family,
                subrepo,

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
                ignoreversion,

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

                    json.dumps(package.extrafields),
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
        self.cursor.execute("""REFRESH MATERIALIZED VIEW CONCURRENTLY url_relations""")

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

        self.cursor.execute("""
            INSERT
                INTO repositories (
                    name,
                    num_maintainers
                ) SELECT
                    repo,
                    count(DISTINCT maintainer)
                FROM (
                    SELECT
                        repo,
                        unnest(maintainers) as maintainer
                    FROM packages
                ) AS temp
                GROUP BY repo
                ON CONFLICT (name)
                DO UPDATE SET
                    num_maintainers = EXCLUDED.num_maintainers
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

        # problems
        self.cursor.execute("""
            INSERT
                INTO problems (
                    repo,
                    name,
                    effname,
                    maintainer,
                    problem
                )
                SELECT DISTINCT
                    packages.repo,
                    packages.name,
                    packages.effname,
                    case when packages.maintainers = '{}' then null else unnest(packages.maintainers) end,
                    'Homepage link "' ||
                        links.url ||
                        '" is dead (' ||
                        CASE
                            WHEN links.status=-1 THEN 'connect timeout'
                            WHEN links.status=-2 THEN 'too many redirects'
                            WHEN links.status=-4 THEN 'cannot connect'
                            WHEN links.status=-5 THEN 'invalid url'
                            WHEN links.status=-6 THEN 'DNS problem'
                            ELSE 'HTTP error ' || links.status
                        END ||
                        ') for more than a month.'
                FROM packages
                    INNER JOIN links ON (packages.homepage = links.url)
                WHERE
                    (links.status IN (-1, -2, -4, -5, -6, 400, 404) OR links.status >= 500) AND
                    (
                        (links.last_success IS NULL AND links.first_extracted < now() - INTERVAL '30' DAY) OR
                        links.last_success < now() - INTERVAL '30' DAY
                    )
        """)

        self.cursor.execute("""
            INSERT
                INTO problems (
                    repo,
                    name,
                    effname,
                    maintainer,
                    problem
                )
                SELECT DISTINCT
                    packages.repo,
                    packages.name,
                    packages.effname,
                    case when packages.maintainers = '{}' then null else unnest(packages.maintainers) end,
                    'Homepage link "' ||
                        links.url ||
                        '" is a permanent redirect to "' ||
                        links.location ||
                        '" and should be updated'
                FROM packages
                    INNER JOIN links ON (packages.homepage = links.url)
                WHERE
                    (
                        links.redirect = 301 AND
                        replace(links.url, 'http://', 'https://') = links.location
                    )
        """)

        self.cursor.execute("""
            INSERT
                INTO problems(repo, name, effname, maintainer, problem)
                SELECT DISTINCT
                    repo,
                    name,
                    effname,
                    case when maintainers = '{}' then null else unnest(maintainers) end,
                    'Homepage link "' || homepage || '" points to Google Code which was discontinued. The link should be updated (probably along with download URLs). If this link is still alive, it may point to a new project homepage.'
                FROM packages
                WHERE
                    homepage SIMILAR TO 'https?://([^/]+.)?googlecode.com(/%)?' OR
                    homepage SIMILAR TO 'https?://code.google.com(/%)?'
        """)

        self.cursor.execute("""
            INSERT
                INTO problems(repo, name, effname, maintainer, problem)
                SELECT DISTINCT
                    repo,
                    name,
                    effname,
                    case when maintainers = '{}' then null else unnest(maintainers) end,
                    'Homepage link "' || homepage || '" points to codeplex which was discontinued. The link should be updated (probably along with download URLs).'
                FROM packages
                WHERE
                    homepage SIMILAR TO 'https?://([^/]+.)?codeplex.com(/%)?'
        """)

        self.cursor.execute("""
            INSERT
                INTO problems(repo, name, effname, maintainer, problem)
                SELECT DISTINCT
                    repo,
                    name,
                    effname,
                    case when maintainers = '{}' then null else unnest(maintainers) end,
                    'Homepage link "' || homepage || '" points to Gna which was discontinued. The link should be updated (probably along with download URLs).'
                FROM packages
                WHERE
                    homepage SIMILAR TO 'https?://([^/]+.)?gna.org(/%)?'
        """)

        self.cursor.execute("""
            INSERT
                INTO repositories (
                    name,
                    num_problems
                ) SELECT
                    repo,
                    count(distinct effname)
                FROM problems
                GROUP BY repo
                ON CONFLICT (name)
                DO UPDATE SET
                    num_problems = EXCLUDED.num_problems
        """)

        # statistics
        self.cursor.execute("""
            UPDATE statistics
            SET
                num_packages = (SELECT count(*) FROM packages),
                num_metapackages = (SELECT count(*) FROM metapackage_repocounts WHERE NOT shadow_only),
                num_problems = (SELECT count(*) FROM problems),
                num_maintainers = (SELECT count(*) FROM maintainers)
        """)

        # cleanup stale links
        self.cursor.execute('DELETE FROM links WHERE last_extracted < now() - INTERVAL \'1\' MONTH')

    def Commit(self):
        self.db.commit()

    def GetMetapackage(self, names):
        self.cursor.execute(
            """
            SELECT
                repo,
                family,
                subrepo,

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
                ignoreversion,

                extrafields
            FROM packages
            WHERE effname {}
            """.format('= ANY (%s)' if isinstance(names, list) else '= %s'),
            (names,)
        )

        return [
            Package(
                repo=row[0],
                family=row[1],
                subrepo=row[2],

                name=row[3],
                effname=row[4],

                version=row[5],
                origversion=row[6],
                effversion=row[7],
                versionclass=row[8],

                maintainers=row[9],
                category=row[10],
                comment=row[11],
                homepage=row[12],
                licenses=row[13],
                downloads=row[14],

                ignore=row[15],
                shadow=row[16],
                ignoreversion=row[17],

                extrafields=row[18],
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
                subrepo,

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
                ignoreversion,

                extrafields
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
                subrepo=row[2],

                name=row[3],
                effname=row[4],

                version=row[5],
                origversion=row[6],
                effversion=row[7],
                versionclass=row[8],

                maintainers=row[9],
                category=row[10],
                comment=row[11],
                homepage=row[12],
                licenses=row[13],
                downloads=row[14],

                ignore=row[15],
                shadow=row[16],
                ignoreversion=row[17],

                extrafields=row[18],
            ) for row in self.cursor.fetchall()
        ]

    def GetPackagesCount(self):
        self.cursor.execute("""SELECT num_packages FROM statistics LIMIT 1""")

        return self.cursor.fetchall()[0][0]

    def GetMetapackagesCount(self):
        self.cursor.execute("""SELECT num_metapackages FROM statistics LIMIT 1""")

        return self.cursor.fetchall()[0][0]

    def GetMaintainersCount(self):
        self.cursor.execute("""SELECT num_maintainers FROM statistics LIMIT 1""")

        return self.cursor.fetchall()[0][0]

    def GetMaintainersRange(self):
        # should use min/max here, but these are slower on pgsql 9.6
        self.cursor.execute('SELECT maintainer FROM maintainers ORDER BY maintainer LIMIT 1')
        min_ = self.cursor.fetchall()[0][0]
        self.cursor.execute('SELECT maintainer FROM maintainers ORDER BY maintainer DESC LIMIT 1')
        max_ = self.cursor.fetchall()[0][0]
        return (min_, max_)

    def GetMaintainers(self, bound=None, reverse=False, search=None, limit=500):
        where = []
        order = 'maintainer'

        query = """
            SELECT
                maintainer,
                num_packages,
                num_packages_outdated
            FROM maintainers
        """
        args = []

        if bound:
            if reverse:
                where.append('maintainer <= %s')
                order = 'maintainer DESC'
                args.append(bound)
            else:
                where.append('maintainer >= %s')
                args.append(bound)

        if search:
            where.append('maintainer LIKE %s')
            args.append('%' + search + '%')

        if where:
            query += ' WHERE ' + ' AND '.join(where)

        if order:
            query += ' ORDER BY ' + order

        if limit:
            query += ' LIMIT %s'
            args.append(limit)

        self.cursor.execute(query, args)

        return sorted([
            {
                'maintainer': row[0],
                'num_packages': row[1],
                'num_packages_outdated': row[2]
            } for row in self.cursor.fetchall()
        ], key=lambda m: m['maintainer'])

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
                now() - last_update,
                num_problems,
                num_maintainers
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
                'since_last_update': row[10],
                'num_problems': row[11],
                'num_maintainers': row[12],
            } for row in self.cursor.fetchall()
        ]

    def GetRepository(self, repo):
        # XXX: remove duplication with GetRepositories()
        self.cursor.execute(
            """
            SELECT
                num_packages,
                num_packages_newest,
                num_packages_outdated,
                num_packages_ignored,
                num_metapackages,
                num_metapackages_unique,
                num_metapackages_newest,
                num_metapackages_outdated,
                last_update at time zone 'UTC',
                now() - last_update,
                num_problems,
                num_maintainers
            FROM repositories
            WHERE name = %s
            """,
            (repo,)
        )

        rows = self.cursor.fetchall()

        if rows:
            row = rows[0]
            return {
                'num_packages': row[0],
                'num_packages_newest': row[1],
                'num_packages_outdated': row[2],
                'num_packages_ignored': row[3],
                'num_metapackages': row[4],
                'num_metapackages_unique': row[5],
                'num_metapackages_newest': row[6],
                'num_metapackages_outdated': row[7],
                'last_update_utc': row[8],
                'since_last_update': row[9],
                'num_problems': row[10],
                'num_maintainers': row[11],
            }
        else:
            return {
                'num_packages': 0,
                'num_packages_newest': 0,
                'num_packages_outdated': 0,
                'num_packages_ignored': 0,
                'num_metapackages': 0,
                'num_metapackages_unique': 0,
                'num_metapackages_newest': 0,
                'num_metapackages_outdated': 0,
                'last_update_utc': None,
                'since_last_update': None,
                'num_problems': 0,
                'num_maintainers': 0,
            }

    def GetRepositoriesHistoryAgo(self, seconds=60 * 60 * 24):
        self.cursor.execute("""
            SELECT
                ts,
                now() - ts,
                snapshot
            FROM repositories_history
            WHERE ts IN (
                SELECT
                    ts
                FROM repositories_history
                WHERE ts < now() - INTERVAL %s
                ORDER BY ts DESC
                LIMIT 1
            )
        """, (datetime.timedelta(seconds=seconds),)
        )

        row = self.cursor.fetchall()[0]

        return {
            'timestamp': row[0],
            'timedelta': row[1],
            **row[2]
        }

    def GetRepositoriesHistoryPeriod(self, seconds=60 * 60 * 24, repo=None):
        repopath = ''
        repoargs = ()

        if repo:
            repopath = '#>%s'
            repoargs = ('{' + repo + '}', )

        self.cursor.execute("""
            SELECT
                ts,
                now() - ts,
                snapshot{}
            FROM repositories_history
            WHERE ts >= now() - INTERVAL %s
            ORDER BY ts
            """.format(repopath),
            repoargs + (datetime.timedelta(seconds=seconds),)
        )

        return [
            {
                'timestamp': row[0],
                'timedelta': row[1],
                'snapshot': row[2]
            }
            for row in self.cursor.fetchall()
        ]

    def GetStatisticsHistoryPeriod(self, seconds=60 * 60 * 24):
        self.cursor.execute("""
            SELECT
                ts,
                now() - ts,
                snapshot
            FROM statistics_history
            WHERE ts >= now() - INTERVAL %s
            ORDER BY ts
        """, (datetime.timedelta(seconds=seconds),)
        )

        return [
            {
                'timestamp': row[0],
                'timedelta': row[1],
                'snapshot': row[2]
            }
            for row in self.cursor.fetchall()
        ]

    def Query(self, query, *args):
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def SnapshotHistory(self):
        self.cursor.execute(
            """
            INSERT
            INTO repositories_history(
                ts,
                snapshot
            )
            SELECT
                now(),
                jsonb_object_agg(snapshot.name, to_jsonb(snapshot) - 'name')
            FROM (
                SELECT
                    name,
                    num_metapackages,
                    num_metapackages_unique,
                    num_metapackages_newest,
                    num_metapackages_outdated,
                    num_problems,
                    num_maintainers
                FROM repositories
            ) AS snapshot
           """
        )

        self.cursor.execute(
            """
            INSERT
            INTO statistics_history(
                ts,
                snapshot
            )
            SELECT
                now(),
                to_jsonb(snapshot)
            FROM (
                SELECT
                    *
                FROM statistics
            ) AS snapshot
           """
        )

    def ExtractLinks(self):
        self.cursor.execute(
            """
            INSERT
            INTO links(
                url,
                first_extracted,
                last_extracted
            ) SELECT
                unnest(downloads),
                now(),
                now()
            FROM packages
            UNION
            SELECT
                homepage,
                now(),
                now()
            FROM packages
            WHERE homepage IS NOT NULL AND repo NOT IN('cpan', 'pypi', 'rubygems', 'hackage', 'cran')
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
    linkcheck_status_dns_error = -6

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
                -- this additional wrap seem to fix query planner somehow
                -- to use index scan on links instead of seq scan, which
                -- makes the query 100x faster; XXX: recheck with postgres 10
                -- or report this?
                SELECT DISTINCT url from (
                    SELECT
                        unnest(downloads) as url
                    FROM packages
                    WHERE effname = %s
                    UNION
                    SELECT
                        homepage as url
                    FROM packages
                    WHERE homepage IS NOT NULL and effname = %s
                ) AS tmp
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

    def GetProblemsCount(self, repo=None, effname=None, maintainer=None):
        where_expr = ''
        args = []

        conditions = []

        if repo:
            conditions.append('repo = %s')
            args.append(repo)
        if effname:
            conditions.append('effname = %s')
            args.append(effname)
        if maintainer:
            conditions.append('maintainer = %s')
            args.append(maintainer)

        if conditions:
            where_expr = 'WHERE ' + ' AND '.join(conditions)

        self.cursor.execute(
            """
            SELECT count(*)
            FROM problems
            {}
            """.format(where_expr),
            args
        )

        return self.cursor.fetchall()[0][0]

    def GetProblems(self, repo=None, effname=None, maintainer=None, limit=None):
        # XXX: eliminate duplication with GetProblemsCount()
        where_expr = ''
        limit_expr = ''
        args = []

        conditions = []

        if repo:
            conditions.append('repo = %s')
            args.append(repo)
        if effname:
            conditions.append('effname = %s')
            args.append(effname)
        if maintainer:
            conditions.append('maintainer = %s')
            args.append(maintainer)

        if conditions:
            where_expr = 'WHERE ' + ' AND '.join(conditions)
        if limit:
            limit_expr = 'LIMIT %s'
            args.append(limit)

        self.cursor.execute(
            """
            SELECT
                repo,
                name,
                effname,
                maintainer,
                problem
            FROM problems
            {}
            ORDER by repo, effname, maintainer
            {}
            """.format(where_expr, limit_expr),
            args
        )

        return [
            {
                'repo': row[0],
                'name': row[1],
                'effname': row[2],
                'maintainer': row[3],
                'problem': row[4],
            }
            for row in self.cursor.fetchall()
        ]

    def AddReport(self, effname, need_verignore, need_split, need_merge, comment):
        self.cursor.execute(
            """
            INSERT
            INTO reports (
                created,
                effname,
                need_verignore,
                need_split,
                need_merge,
                comment
            ) VALUES (
                now(),
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                effname,
                need_verignore,
                need_split,
                need_merge,
                comment
            )
        )

    def GetReportsCount(self, effname):
        self.cursor.execute('SELECT count(*) FROM reports WHERE effname = %s', (effname, ))
        return self.cursor.fetchall()[0][0]

    def GetReports(self, effname):
        self.cursor.execute(
            """
            SELECT
                id,
                now() - created,
                effname,
                need_verignore,
                need_split,
                need_merge,
                comment,
                reply,
                accepted
            FROM reports
            WHERE effname = %s
            ORDER BY created desc
            """,
            (effname, )
        )

        return [
            {
                'id': row[0],
                'created_ago': row[1],
                'effname': row[2],
                'need_verignore': row[3],
                'need_split': row[4],
                'need_merge': row[5],
                'comment': row[6],
                'reply': row[7],
                'accepted': row[8],
            }
            for row in self.cursor.fetchall()
        ]

    def GetRelatedMetapackages(self, name, limit=500):
        self.cursor.execute(
            """
            WITH RECURSIVE r AS (
                    SELECT
                        effname,
                        url
                    FROM url_relations
                    WHERE effname=%s
                UNION
                    SELECT
                        url_relations.effname,
                        url_relations.url
                    FROM url_relations
                    JOIN r ON
                        url_relations.effname = r.effname OR url_relations.url = r.url
            ) SELECT DISTINCT effname FROM r ORDER by effname LIMIT %s
            """,
            (name, limit)
        )

        return [
            row[0] for row in self.cursor.fetchall()
        ]
