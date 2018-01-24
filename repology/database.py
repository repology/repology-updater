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
    def __init__(self, dsn, readonly=True, autocommit=False):
        self.db = psycopg2.connect(dsn)
        self.db.set_session(readonly=readonly, autocommit=autocommit)

    def Request(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

    def RequestSingleValue(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            row = cursor.fetchone()

            if row is None:
                return None

            return row[0]

    def RequestSingleAsDict(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            row = cursor.fetchone()

            if row is None:
                return None

            names = [desc.name for desc in cursor.description]

            return dict(zip(names, row))

    def RequestManyAsSingleColumnArray(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            return [row[0] for row in cursor.fetchall()]

    def RequestManyAsDictOfDicts(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            names = [desc.name for desc in cursor.description]

            return {row[0]: dict(zip(names[1:], row[1:])) for row in cursor.fetchall()}

    def RequestManyAsDicts(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            names = [desc.name for desc in cursor.description]

            return [dict(zip(names, row)) for row in cursor.fetchall()]

    def RequestManyAsPackages(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)

            names = [desc.name for desc in cursor.description]

            return [Package(**dict(zip(names, row))) for row in cursor.fetchall()]

    def CreateSchema(self):
        with self.db.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS packages CASCADE')
            cursor.execute('DROP TABLE IF EXISTS repositories CASCADE')
            cursor.execute('DROP TABLE IF EXISTS repositories_history CASCADE')
            cursor.execute('DROP TABLE IF EXISTS statistics CASCADE')
            cursor.execute('DROP TABLE IF EXISTS statistics_history CASCADE')
            cursor.execute('DROP TABLE IF EXISTS totals_history CASCADE')
            cursor.execute('DROP TABLE IF EXISTS links CASCADE')
            cursor.execute('DROP TABLE IF EXISTS problems CASCADE')
            cursor.execute('DROP TABLE IF EXISTS reports CASCADE')

            cursor.execute("""
                CREATE TABLE packages (
                    repo text not null,
                    family text not null,
                    subrepo text,

                    name text not null,
                    effname text not null,

                    version text not null,
                    origversion text,
                    versionclass smallint,

                    maintainers text[],
                    category text,
                    comment text,
                    homepage text,
                    licenses text[],
                    downloads text[],

                    flags smallint not null,
                    shadow bool not null,
                    verfixed bool not null,

                    flavors text[],

                    extrafields jsonb not null
                )
            """)

            cursor.execute('CREATE INDEX ON packages(effname)')

            # This should be used in queries instead of packages table
            # everywhere where shadow metapackages need to be ignored
            #
            # XXX: may also investigate using NOT IN (HAVING bool_and())
            # variant of this query
            cursor.execute("""
                CREATE VIEW packages_ns AS
                    SELECT * FROM PACKAGES
                    WHERE effname IN (
                        SELECT effname
                        FROM packages
                        GROUP BY effname
                        HAVING NOT bool_and(shadow)
                    )
            """)

            # repositories
            cursor.execute("""
                CREATE TABLE repositories (
                    name text not null primary key,

                    num_packages integer not null default 0,
                    num_packages_newest integer not null default 0,
                    num_packages_outdated integer not null default 0,
                    num_packages_ignored integer not null default 0,
                    num_packages_unique integer not null default 0,
                    num_packages_devel integer not null default 0,
                    num_packages_legacy integer not null default 0,
                    num_packages_incorrect integer not null default 0,
                    num_packages_untrusted integer not null default 0,
                    num_packages_noscheme integer not null default 0,
                    num_packages_rolling integer not null default 0,

                    num_metapackages integer not null default 0,
                    num_metapackages_unique integer not null default 0,
                    num_metapackages_newest integer not null default 0,
                    num_metapackages_outdated integer not null default 0,
                    num_metapackages_comparable integer not null default 0,

                    last_update timestamp with time zone,

                    num_problems integer not null default 0,
                    num_maintainers integer not null default 0
                )
            """)

            # repository_history
            cursor.execute("""
                CREATE TABLE repositories_history (
                    ts timestamp with time zone not null primary key,
                    snapshot jsonb not null
                )
            """)

            # statistics
            cursor.execute("""
                CREATE TABLE statistics (
                    num_packages integer not null default 0,
                    num_metapackages integer not null default 0,
                    num_problems integer not null default 0,
                    num_maintainers integer not null default 0
                )
            """)

            cursor.execute("""
                INSERT INTO statistics VALUES(DEFAULT)
            """)

            # statistics_history
            cursor.execute("""
                CREATE TABLE statistics_history (
                    ts timestamp with time zone not null primary key,
                    snapshot jsonb not null
                )
            """)

            # repo counts per metapackage
            cursor.execute("""
                CREATE MATERIALIZED VIEW metapackage_repocounts AS
                    SELECT
                        effname,
                        count(DISTINCT repo)::smallint AS num_repos,
                        count(DISTINCT family)::smallint AS num_families,
                        count(DISTINCT repo) FILTER (WHERE versionclass = 1)::smallint AS num_repos_newest,
                        count(DISTINCT family) FILTER (WHERE versionclass = 1)::smallint AS num_families_newest,
                        bool_and(shadow) AS shadow_only
                    FROM packages
                    GROUP BY effname
                    ORDER BY effname
                WITH DATA
            """)

            cursor.execute('CREATE UNIQUE INDEX ON metapackage_repocounts(effname)')
            cursor.execute('CREATE INDEX ON metapackage_repocounts(num_repos)')
            cursor.execute('CREATE INDEX ON metapackage_repocounts(num_families)')
            cursor.execute('CREATE INDEX ON metapackage_repocounts(shadow_only, num_families)')

            # package class counts aggregated for each metapackage/repo
            cursor.execute("""
                CREATE MATERIALIZED VIEW repo_metapackages
                    AS
                        SELECT
                            repo,
                            effname,
                            count(*)::smallint AS num_packages,
                            count(*) FILTER (WHERE versionclass = 1)::smallint AS num_packages_newest,
                            count(*) FILTER (WHERE versionclass = 2)::smallint AS num_packages_outdated,
                            count(*) FILTER (WHERE versionclass = 3)::smallint AS num_packages_ignored,
                            count(*) FILTER (WHERE versionclass = 4)::smallint AS num_packages_unique,
                            count(*) FILTER (WHERE versionclass = 5)::smallint AS num_packages_devel,
                            count(*) FILTER (WHERE versionclass = 6)::smallint AS num_packages_legacy,
                            count(*) FILTER (WHERE versionclass = 7)::smallint AS num_packages_incorrect,
                            count(*) FILTER (WHERE versionclass = 8)::smallint AS num_packages_untrusted,
                            count(*) FILTER (WHERE versionclass = 9)::smallint AS num_packages_noscheme,
                            count(*) FILTER (WHERE versionclass = 10)::smallint AS num_packages_rolling,
                            max(num_families) = 1 as unique
                        FROM packages INNER JOIN metapackage_repocounts USING(effname)
                        WHERE NOT shadow_only
                        GROUP BY effname,repo
                    WITH DATA
            """)

            cursor.execute('CREATE UNIQUE INDEX ON repo_metapackages(repo, effname)')
            cursor.execute('CREATE INDEX ON repo_metapackages(effname)')
            cursor.execute('CREATE INDEX repo_metapackages_effname_trgm ON repo_metapackages USING gin (effname gin_trgm_ops)')

            # metapackages per category
            cursor.execute("""
                CREATE MATERIALIZED VIEW category_metapackages
                    AS
                        SELECT
                            category,
                            effname,
                            max(num_families) = 1 as unique
                        FROM packages INNER JOIN metapackage_repocounts USING(effname)
                        WHERE NOT shadow_only
                        GROUP BY effname,category
                    WITH DATA
            """)

            cursor.execute('CREATE UNIQUE INDEX ON category_metapackages(category, effname)')
            cursor.execute('CREATE INDEX ON category_metapackages(effname)')

            # maintainer_metapackages
            cursor.execute("""
                CREATE MATERIALIZED VIEW maintainer_metapackages
                    AS
                        SELECT
                            unnest(maintainers) as maintainer,
                            effname,
                            count(1)::smallint AS num_packages,
                            count(*) FILTER (WHERE versionclass = 1)::smallint AS num_packages_newest,
                            count(*) FILTER (WHERE versionclass = 2)::smallint AS num_packages_outdated,
                            count(*) FILTER (WHERE versionclass = 3)::smallint AS num_packages_ignored,
                            count(*) FILTER (WHERE versionclass = 4)::smallint AS num_packages_unique,
                            count(*) FILTER (WHERE versionclass = 5)::smallint AS num_packages_devel,
                            count(*) FILTER (WHERE versionclass = 6)::smallint AS num_packages_legacy,
                            count(*) FILTER (WHERE versionclass = 7)::smallint AS num_packages_incorrect,
                            count(*) FILTER (WHERE versionclass = 8)::smallint AS num_packages_untrusted,
                            count(*) FILTER (WHERE versionclass = 9)::smallint AS num_packages_noscheme,
                            count(*) FILTER (WHERE versionclass = 10)::smallint AS num_packages_rolling
                        FROM packages
                        GROUP BY maintainer, effname
                    WITH DATA
            """)

            cursor.execute('CREATE UNIQUE INDEX ON maintainer_metapackages(maintainer, effname)')
            cursor.execute('CREATE INDEX ON maintainer_metapackages(effname)')

            # maintainers
            cursor.execute("""
                CREATE MATERIALIZED VIEW maintainers AS
                    SELECT *
                    FROM
                    (
                        SELECT
                            unnest(maintainers) AS maintainer,
                            count(1)::integer AS num_packages,
                            count(DISTINCT effname)::integer AS num_metapackages,
                            count(DISTINCT effname) FILTER(WHERE versionclass = 2)::integer AS num_metapackages_outdated,
                            count(*) FILTER (WHERE versionclass = 1)::integer AS num_packages_newest,
                            count(*) FILTER (WHERE versionclass = 2)::integer AS num_packages_outdated,
                            count(*) FILTER (WHERE versionclass = 3)::integer AS num_packages_ignored,
                            count(*) FILTER (WHERE versionclass = 4)::integer AS num_packages_unique,
                            count(*) FILTER (WHERE versionclass = 5)::integer AS num_packages_devel,
                            count(*) FILTER (WHERE versionclass = 6)::integer AS num_packages_legacy,
                            count(*) FILTER (WHERE versionclass = 7)::integer AS num_packages_incorrect,
                            count(*) FILTER (WHERE versionclass = 8)::integer AS num_packages_untrusted,
                            count(*) FILTER (WHERE versionclass = 9)::integer AS num_packages_noscheme,
                            count(*) FILTER (WHERE versionclass = 10)::integer AS num_packages_rolling
                        FROM packages
                        GROUP BY maintainer
                    ) AS packages_subreq
                    LEFT JOIN
                    (
                        SELECT
                            maintainer,
                            json_object_agg(repo, numrepopkg) AS repository_package_counts,
                            json_object_agg(repo, numrepometapkg) AS repository_metapackage_counts
                        FROM
                        (
                            SELECT
                                unnest(maintainers) AS maintainer,
                                repo,
                                count(*) AS numrepopkg,
                                count(DISTINCT effname) AS numrepometapkg
                            FROM packages
                            GROUP BY maintainer, repo
                        ) AS repositories_subreq_inner
                        GROUP BY maintainer
                    ) AS repositories_subreq
                    USING(maintainer)
                    LEFT JOIN
                    (
                        SELECT
                            maintainer,
                            json_object_agg(category, numcatmetapkg) AS category_metapackage_counts
                        FROM
                        (
                            SELECT
                                unnest(maintainers) AS maintainer,
                                category,
                                count(DISTINCT effname) AS numcatmetapkg
                            FROM packages
                            WHERE category IS NOT NULL
                            GROUP BY maintainer, category
                        ) AS categories_subreq_innser
                        GROUP BY maintainer
                    ) AS categories_subreq
                    USING(maintainer)
                WITH DATA
            """)

            cursor.execute('CREATE UNIQUE INDEX ON maintainers(maintainer)')

            # links for link checker
            cursor.execute("""
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
            cursor.execute("""
                CREATE TABLE problems (
                    repo text not null,
                    name text not null,
                    effname text not null,
                    maintainer text,
                    problem text not null
                )
            """)

            cursor.execute('CREATE INDEX ON problems(effname)')
            cursor.execute('CREATE INDEX ON problems(repo, effname)')
            cursor.execute('CREATE INDEX ON problems(maintainer)')

            # reports
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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

            cursor.execute('CREATE INDEX ON reports(effname)')

            # url_relations
            cursor.execute("""
                CREATE MATERIALIZED VIEW url_relations AS
                    SELECT DISTINCT
                        effname,
                        regexp_replace(regexp_replace(homepage, '/?([#?].*)?$', ''), '^https?://(www\\.)?', '') as url
                    FROM packages
                    WHERE homepage ~ '^https?://'
                WITH DATA
            """)

            cursor.execute('CREATE UNIQUE INDEX ON url_relations(effname, url)')  # we only need url here because we need unique index for concurrent refresh
            cursor.execute('CREATE INDEX ON url_relations(url)')

    def Clear(self):
        with self.db.cursor() as cursor:
            cursor.execute('DELETE FROM packages')
            cursor.execute(
                """
                UPDATE repositories
                SET
                    num_packages = 0,
                    num_packages_newest = 0,
                    num_packages_outdated = 0,
                    num_packages_ignored = 0,
                    num_packages_unique = 0,
                    num_packages_devel = 0,
                    num_packages_legacy = 0,
                    num_packages_incorrect = 0,
                    num_packages_untrusted = 0,
                    num_packages_noscheme = 0,
                    num_packages_rolling = 0,
                    num_metapackages = 0,
                    num_metapackages_unique = 0,
                    num_metapackages_newest = 0,
                    num_metapackages_outdated = 0,
                    num_metapackages_comparable = 0,
                    num_problems = 0,
                    num_maintainers = 0
                """
            )
            cursor.execute('DELETE FROM problems')
            cursor.execute(
                """
                UPDATE statistics
                SET
                    num_packages = 0,
                    num_metapackages = 0,
                    num_problems = 0,
                    num_maintainers = 0
                """
            )

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

    def MarkRepositoriesUpdated(self, reponames):
        with self.db.cursor() as cursor:
            cursor.executemany(
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
        with self.db.cursor() as cursor:
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY metapackage_repocounts')
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY repo_metapackages')
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY category_metapackages')
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY maintainer_metapackages')
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY maintainers')
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY url_relations')

            # package stats
            cursor.execute("""
                INSERT
                    INTO repositories (
                        name,
                        num_packages,
                        num_packages_newest,
                        num_packages_outdated,
                        num_packages_ignored,
                        num_packages_unique,
                        num_packages_devel,
                        num_packages_legacy,
                        num_packages_incorrect,
                        num_packages_untrusted,
                        num_packages_noscheme,
                        num_packages_rolling
                    ) SELECT
                        repo,
                        sum(num_packages),
                        sum(num_packages_newest),
                        sum(num_packages_outdated),
                        sum(num_packages_ignored),
                        sum(num_packages_unique),
                        sum(num_packages_devel),
                        sum(num_packages_legacy),
                        sum(num_packages_incorrect),
                        sum(num_packages_untrusted),
                        sum(num_packages_noscheme),
                        sum(num_packages_rolling)
                    FROM repo_metapackages
                    GROUP BY repo
                    ON CONFLICT (name)
                    DO UPDATE SET
                        num_packages = EXCLUDED.num_packages,
                        num_packages_newest = EXCLUDED.num_packages_newest,
                        num_packages_outdated = EXCLUDED.num_packages_outdated,
                        num_packages_ignored = EXCLUDED.num_packages_ignored,
                        num_packages_unique = EXCLUDED.num_packages_unique,
                        num_packages_devel = EXCLUDED.num_packages_devel,
                        num_packages_legacy = EXCLUDED.num_packages_legacy,
                        num_packages_incorrect = EXCLUDED.num_packages_incorrect,
                        num_packages_untrusted = EXCLUDED.num_packages_untrusted,
                        num_packages_noscheme = EXCLUDED.num_packages_noscheme,
                        num_packages_rolling = EXCLUDED.num_packages_rolling
            """)

            cursor.execute("""
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
            cursor.execute("""
                INSERT
                    INTO repositories (
                        name,
                        num_metapackages,
                        num_metapackages_unique,
                        num_metapackages_newest,
                        num_metapackages_outdated,
                        num_metapackages_comparable
                    ) SELECT
                        repo,
                        count(*),
                        count(*) FILTER (WHERE repo_metapackages.unique),
                        count(*) FILTER (WHERE NOT repo_metapackages.unique AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0),
                        count(*) FILTER (WHERE num_packages_outdated > 0),
                        count(*) FILTER (WHERE
                            -- newest
                            (NOT repo_metapackages.unique AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) OR
                            -- outdated
                            (num_packages_outdated > 0) OR
                            -- problematic subset
                            (num_packages_incorrect > 0)
                        )
                    FROM repo_metapackages
                    GROUP BY repo
                    ON CONFLICT (name)
                    DO UPDATE SET
                        num_metapackages = EXCLUDED.num_metapackages,
                        num_metapackages_unique = EXCLUDED.num_metapackages_unique,
                        num_metapackages_newest = EXCLUDED.num_metapackages_newest,
                        num_metapackages_outdated = EXCLUDED.num_metapackages_outdated,
                        num_metapackages_comparable = EXCLUDED.num_metapackages_comparable
            """)

            # problems
            cursor.execute("""
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
                        unnest(case when packages.maintainers = '{}' then '{null}' else packages.maintainers end),
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

            cursor.execute("""
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
                        unnest(case when packages.maintainers = '{}' then '{null}' else packages.maintainers end),
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

            cursor.execute("""
                INSERT
                    INTO problems(repo, name, effname, maintainer, problem)
                    SELECT DISTINCT
                        repo,
                        name,
                        effname,
                        unnest(case when packages.maintainers = '{}' then '{null}' else packages.maintainers end),
                        'Homepage link "' || homepage || '" points to Google Code which was discontinued. The link should be updated (probably along with download URLs). If this link is still alive, it may point to a new project homepage.'
                    FROM packages
                    WHERE
                        homepage SIMILAR TO 'https?://([^/]+.)?googlecode.com(/%)?' OR
                        homepage SIMILAR TO 'https?://code.google.com(/%)?'
            """)

            cursor.execute("""
                INSERT
                    INTO problems(repo, name, effname, maintainer, problem)
                    SELECT DISTINCT
                        repo,
                        name,
                        effname,
                        unnest(case when packages.maintainers = '{}' then '{null}' else packages.maintainers end),
                        'Homepage link "' || homepage || '" points to codeplex which was discontinued. The link should be updated (probably along with download URLs).'
                    FROM packages
                    WHERE
                        homepage SIMILAR TO 'https?://([^/]+.)?codeplex.com(/%)?'
            """)

            cursor.execute("""
                INSERT
                    INTO problems(repo, name, effname, maintainer, problem)
                    SELECT DISTINCT
                        repo,
                        name,
                        effname,
                        unnest(case when packages.maintainers = '{}' then '{null}' else packages.maintainers end),
                        'Homepage link "' || homepage || '" points to Gna which was discontinued. The link should be updated (probably along with download URLs).'
                    FROM packages
                    WHERE
                        homepage SIMILAR TO 'https?://([^/]+.)?gna.org(/%)?'
            """)

            cursor.execute("""
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
            cursor.execute("""
                UPDATE statistics
                SET
                    num_packages = (SELECT count(*) FROM packages),
                    num_metapackages = (SELECT count(*) FROM metapackage_repocounts WHERE NOT shadow_only),
                    num_problems = (SELECT count(*) FROM problems),
                    num_maintainers = (SELECT count(*) FROM maintainers)
            """)

            # cleanup stale links
            cursor.execute('DELETE FROM links WHERE last_extracted < now() - INTERVAL \'1\' MONTH')

    def Commit(self):
        self.db.commit()

    def GetMetapackage(self, names):
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
            WHERE effname {}
            """.format('= ANY (%s)' if isinstance(names, list) else '= %s'),
            names
        )

    def GetMetapackages(self, request, limit=500):
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

    def GetRelatedMetapackages(self, name, limit=500):
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
                )
                SELECT DISTINCT
                    effname
                FROM r
                ORDER BY effname
                LIMIT %s
            )
            """,
            name,
            limit
        )

    def GetPackagesCount(self):
        return self.RequestSingleValue('SELECT num_packages FROM statistics LIMIT 1')

    def GetMetapackagesCount(self):
        return self.RequestSingleValue('SELECT num_metapackages FROM statistics LIMIT 1')

    def GetMaintainersCount(self):
        return self.RequestSingleValue('SELECT num_maintainers FROM statistics LIMIT 1')

    def GetMaintainersRange(self):
        # could use min/max here, but these are slower on pgsql 9.6
        return (
            self.RequestSingleValue('SELECT maintainer FROM maintainers ORDER BY maintainer LIMIT 1'),
            self.RequestSingleValue('SELECT maintainer FROM maintainers ORDER BY maintainer DESC LIMIT 1')
        )

    def GetMaintainers(self, bound=None, reverse=False, search=None, limit=500):
        where = []
        tail = ''

        args = []

        order = 'maintainer'

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

        if limit:
            tail = 'LIMIT %s'
            args.append(limit)

        return self.RequestManyAsDicts(
            """
            SELECT
                *
            FROM
            (
                SELECT
                    maintainer,
                    num_packages,
                    num_metapackages,
                    num_metapackages_outdated
                FROM maintainers
                {}
                ORDER BY {}
                {}
            ) AS tmp
            ORDER BY maintainer
            """.format(
                'WHERE ' + ' AND '.join(where) if where else '',
                order,
                tail
            ),
            *args
        )

    def GetMaintainerInformation(self, maintainer):
        return self.RequestSingleAsDict(
            """
            SELECT
                num_packages,
                num_packages_newest,
                num_packages_outdated,
                num_packages_ignored,
                num_packages_unique,
                num_packages_devel,
                num_packages_legacy,
                num_packages_incorrect,
                num_packages_untrusted,
                num_packages_noscheme,
                num_packages_rolling,
                num_metapackages,
                num_metapackages_outdated,
                repository_package_counts,
                repository_metapackage_counts,
                category_metapackage_counts
            FROM maintainers
            WHERE maintainer = %s
            """,
            maintainer
        )

    def GetMaintainerMetapackages(self, maintainer, limit=1000):
        return self.RequestManyAsSingleColumnArray(
            """
            SELECT
                effname
            FROM maintainer_metapackages
            WHERE maintainer = %s
            ORDER BY effname
            LIMIT %s
            """,
            maintainer,
            limit
        )

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
        # - num_metapackages_common is |M⋂C|
        # - num_metapackages is |C|
        # - sub-select just gets |M|
        # - the divisor thus is |M⋃C| = |M| + |C| - |M⋂C|
        return self.RequestManyAsDicts(
            """
            SELECT
                maintainer,
                num_metapackages_common AS count,
                100.0 * num_metapackages_common / (
                    num_metapackages - num_metapackages_common + (
                        SELECT num_metapackages
                        FROM maintainers
                        WHERE maintainer=%s
                    )
                ) AS match
            FROM
                (
                    SELECT
                        maintainer,
                        count(*) AS num_metapackages_common
                    FROM
                        maintainer_metapackages
                    WHERE
                        maintainer != %s AND
                        effname IN (
                            SELECT
                                effname
                            FROM maintainer_metapackages
                            WHERE maintainer=%s
                        )
                    GROUP BY maintainer
                ) AS intersecting_counts
                INNER JOIN maintainers USING(maintainer)
            ORDER BY match DESC
            LIMIT %s
            """,
            maintainer,
            maintainer,
            maintainer,
            limit
        )

    def GetRepositories(self):
        return self.RequestManyAsDicts(
            """
            SELECT
                name,
                num_packages,
                num_packages_newest,
                num_packages_outdated,
                num_packages_ignored,
                num_packages_unique,
                num_packages_devel,
                num_packages_legacy,
                num_packages_incorrect,
                num_packages_untrusted,
                num_packages_noscheme,
                num_packages_rolling,
                num_metapackages,
                num_metapackages_unique,
                num_metapackages_newest,
                num_metapackages_outdated,
                num_metapackages_comparable,
                last_update at time zone 'UTC' AS last_update_utc,
                now() - last_update AS since_last_update,
                num_problems,
                num_maintainers
            FROM repositories
        """)

    def GetRepository(self, repo):
        return self.RequestSingleAsDict(
            """
            SELECT
                num_packages,
                num_packages_newest,
                num_packages_outdated,
                num_packages_ignored,
                num_packages_unique,
                num_packages_devel,
                num_packages_legacy,
                num_packages_incorrect,
                num_packages_untrusted,
                num_packages_noscheme,
                num_packages_rolling,
                num_metapackages,
                num_metapackages_unique,
                num_metapackages_newest,
                num_metapackages_outdated,
                num_metapackages_comparable,
                last_update at time zone 'UTC' AS last_update_utc,
                now() - last_update AS since_last_update,
                num_problems,
                num_maintainers
            FROM repositories
            WHERE name = %s
            """,
            repo,
        )

    def GetRepositoriesHistoryAgo(self, seconds=60 * 60 * 24):
        return self.RequestSingleAsDict(
            """
            SELECT
                ts AS timestamp,
                now() - ts AS timedelta,
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
            """,
            datetime.timedelta(seconds=seconds),
        )

    def GetRepositoriesHistoryPeriod(self, seconds=60 * 60 * 24, repo=None):
        repopath = ''
        repoargs = ()

        if repo:
            repopath = '#>%s'
            repoargs = ('{' + repo + '}', )

        return self.RequestManyAsDicts(
            """
            SELECT
                ts AS timestamp,
                now() - ts AS timedelta,
                snapshot{} AS snapshot
            FROM repositories_history
            WHERE ts >= now() - INTERVAL %s
            ORDER BY ts
            """.format(repopath),
            *repoargs,
            datetime.timedelta(seconds=seconds)
        )

    def GetStatisticsHistoryPeriod(self, seconds=60 * 60 * 24):
        return self.RequestManyAsDicts(
            """
            SELECT
                ts AS timestamp,
                now() - ts AS timedelta,
                snapshot
            FROM statistics_history
            WHERE ts >= now() - INTERVAL %s
            ORDER BY ts
            """,
            datetime.timedelta(seconds=seconds)
        )

    def Query(self, query, *args):
        with self.db.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()

    def SnapshotHistory(self):
        self.Request(
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
                    num_metapackages_comparable,
                    num_problems,
                    num_maintainers
                FROM repositories
            ) AS snapshot
           """
        )

        self.Request(
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
        self.Request(
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
            conditions.append('status = 200')

        conditions_expr = ''
        limit_expr = ''

        if conditions:
            conditions_expr = 'WHERE ' + ' AND '.join(conditions)

        if limit:
            limit_expr = 'LIMIT %s'
            args.append(limit)

        return self.RequestManyAsSingleColumnArray(
            """
            SELECT
                url
            FROM links
            {}
            ORDER BY url
            {}
            """.format(conditions_expr, limit_expr),
            *args
        )

    linkcheck_status_timeout = -1
    linkcheck_status_too_many_redirects = -2
    linkcheck_status_unknown_error = -3
    linkcheck_status_cannot_connect = -4
    linkcheck_status_invalid_url = -5
    linkcheck_status_dns_error = -6

    def UpdateLinkStatus(self, url, status, redirect=None, size=None, location=None):
        success = status == 200

        self.Request(
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
            success,
            not success,
            status,
            redirect,
            size,
            location,
            url
        )

    def GetMetapackageLinkStatuses(self, name):
        return self.RequestManyAsDictOfDicts(
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
            name,
            name
        )

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

        return self.RequestSingleValue(
            """
            SELECT count(*)
            FROM problems
            {}
            """.format(where_expr),
            *args
        )

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

        return self.RequestManyAsDicts(
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
            *args
        )

    def AddReport(self, effname, need_verignore, need_split, need_merge, comment):
        self.Request(
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
            effname,
            need_verignore,
            need_split,
            need_merge,
            comment
        )

    def GetReportsCount(self, effname):
        return self.RequestSingleValue('SELECT count(*) FROM reports WHERE effname = %s', effname)

    def GetReports(self, effname):
        return self.RequestManyAsDicts(
            """
            SELECT
                id,
                now() - created AS created_ago,
                effname,
                need_verignore,
                need_split,
                need_merge,
                comment,
                reply,
                accepted
            FROM reports
            WHERE effname = %s
            ORDER BY created DESC
            """,
            effname
        )
