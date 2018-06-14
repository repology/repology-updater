# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repologyapp.db import get_db

__all__ = [
    'RepositoryMetadata'
]


class RepositoryMetadata:
    AUTOREFRESH_PERIOD = datetime.timedelta(seconds=300)

    def __init__(self):
        self.repos = []
        self.by_name = {}
        self.update_time = None

    def update(self):
        self.repos = get_db().get_repositories_metadata()  # already sorted by sortname
        self.by_name = {repo['name']: repo for repo in self.repos}
        self.update_time = datetime.datetime.now()

    def is_stale(self):
        return self.update_time is None or datetime.datetime.now() - self.update_time > RepositoryMetadata.AUTOREFRESH_PERIOD

    def __getitem__(self, reponame):
        if reponame not in self.by_name or self.is_stale():
            self.update()

            if reponame not in self.by_name:
                raise KeyError('No metadata for repository ' + reponame)

        return self.by_name[reponame]

    def __contains__(self, reponame):
        if self.is_stale():
            self.update()
        return reponame in self.by_name

    def all_names(self):
        if self.is_stale():
            self.update()
        return [repo['name'] for repo in self.repos]

    def active_names(self):
        if self.is_stale():
            self.update()
        return [repo['name'] for repo in self.repos if repo['active']]
