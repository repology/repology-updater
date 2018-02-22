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


class MetapackageRequest:
    def __init__(self):
        # effname filtering
        self.pivot = None
        self.reverse = False

        self.search = None

        # maintainer (maintainer_metapackages)
        self.maintainer = None

        # num families (metapackage_repocounts)
        self.minspread = None
        self.maxspread = None

        # repos (repo_metapackages)
        self.inrepo = None
        self.notinrepo = None

        # category
        self.category = None

        # flags
        self.newest = False
        self.outdated = False
        self.newest_single_repo = False
        self.newest_single_family = False
        self.problematic = False

    def Bound(self, bound):
        if not bound:
            pass
        elif bound.startswith('..'):
            self.NameTo(bound[2:])
        else:
            self.NameFrom(bound)

    def NameFrom(self, name):
        if self.pivot:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.pivot = name
            self.reverse = False

    def NameTo(self, name):
        if self.pivot:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.pivot = name
            self.reverse = True

    def NameSubstring(self, substring):
        if self.search:
            raise RuntimeError('duplicate effname substring condition')
        self.search = substring

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
        if self.minspread:
            raise RuntimeError('duplicate more families condition')
        self.minspread = num

    def MaxFamilies(self, num):
        if self.maxspread:
            raise RuntimeError('duplicate less families condition')
        self.maxspread = num

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


class Database:
    def __init__(self, dsn, querymgr, readonly=True, autocommit=False, application_name=None):
        self.db = psycopg2.connect(dsn, application_name=application_name)
        self.db.set_session(readonly=readonly, autocommit=autocommit)
        querymgr.InjectQueries(self, self.db)
        self.queries = self  # XXX: switch to calling queries directly and remove

    def commit(self):
        self.db.commit()

    def add_packages(self, packages):
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

    linkcheck_status_timeout = -1
    linkcheck_status_too_many_redirects = -2
    linkcheck_status_unknown_error = -3
    linkcheck_status_cannot_connect = -4
    linkcheck_status_invalid_url = -5
    linkcheck_status_dns_error = -6
