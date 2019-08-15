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
from typing import Any, ClassVar, Dict, Iterable, List, Optional

from repologyapp.db import get_db


__all__ = [
    'RepositoryMetadata'
]


class RepositoryMetadata:
    AUTOREFRESH_PERIOD: ClassVar[datetime.timedelta] = datetime.timedelta(seconds=300)

    _repos: List[Dict[str, Any]]
    _by_name: Dict[str, Dict[str, Any]]
    _update_time: Optional[datetime.datetime]

    def __init__(self) -> None:
        self._repos = []
        self._by_name = {}
        self._update_time = None

    def update(self) -> None:
        self._repos = get_db().get_repositories_metadata()  # already sorted by sortname
        self._by_name = {repo['name']: repo for repo in self._repos}
        self._update_time = datetime.datetime.now()

    def is_stale(self) -> bool:
        return self._update_time is None or datetime.datetime.now() - self._update_time > RepositoryMetadata.AUTOREFRESH_PERIOD

    def __getitem__(self, reponame: str) -> Dict[str, Any]:
        if reponame not in self._by_name or self.is_stale():
            self.update()

            if reponame not in self._by_name:
                raise KeyError('No metadata for repository ' + reponame)

        return self._by_name[reponame]

    def __contains__(self, reponame: str) -> bool:
        if self.is_stale():
            self.update()
        return reponame in self._by_name

    def all_names(self) -> List[str]:
        if self.is_stale():
            self.update()
        return [repo['name'] for repo in self._repos]

    def active_names(self) -> List[str]:
        if self.is_stale():
            self.update()
        return [repo['name'] for repo in self._repos if repo['active']]

    def sorted_active_names(self, names: Iterable[str]) -> List[str]:
        if self.is_stale():
            self.update()
        names_set = set(names)
        return [repo['name'] for repo in self._repos if repo['active'] and repo['name'] in names_set]
