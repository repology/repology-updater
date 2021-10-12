# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import copy
from enum import Enum
from typing import Any, Collection, Iterable, Optional, TYPE_CHECKING, overload

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass

from repology.yamlloader import YamlConfig


RepositoryNameList = Optional[Collection[str]]  # XXX: can't use |-union yet, see https://github.com/python/mypy/issues/11280
RepositoryMetadata = dict[str, Any]


def _subst_source_recursively(container: dict[str, Any] | list[Any], name: str) -> None:
    key_iter: Iterable[Any]
    if isinstance(container, list):
        key_iter = range(len(container))
    elif isinstance(container, dict):
        key_iter = container.keys()
    else:
        return

    for key in key_iter:
        if isinstance(container[key], str):
            container[key] = container[key].replace('{source}', name)
        elif isinstance(container[key], list) or isinstance(container[key], dict):
            _subst_source_recursively(container[key], name)


@overload
def _parse_duration(arg: str | int) -> int:
    pass


@overload
def _parse_duration(arg: None) -> None:
    pass


def _parse_duration(arg: str | int | None) -> int | None:
    if not isinstance(arg, str):
        return arg
    elif arg.endswith('m'):
        return int(arg[:-1]) * 60
    elif arg.endswith('h'):
        return int(arg[:-1]) * 60 * 60
    elif arg.endswith('d'):
        return int(arg[:-1]) * 60 * 60 * 24
    else:
        return int(arg)


def _listify(arg: Any) -> list[Any]:
    if not isinstance(arg, list):
        return [arg]
    else:
        return arg


class RepositoryType(str, Enum):
    REPOSITORY = 'repository'
    SITE = 'site'
    MODULES = 'modules'


@dataclass
class Repository:
    name: str
    sortname: str
    singular: str
    type: RepositoryType  # noqa
    desc: str
    statsgroup: str
    family: str
    ruleset: list[str]
    color: str
    valid_till: Optional[str]
    default_maintainer: Optional[str]
    update_period: int
    minpackages: int

    shadow: bool
    incomplete: bool

    repolinks: list[Any]
    packagelinks: list[Any]

    groups: list[str]

    sources: list[Any]


class RepositoryManager:
    _repositories: list[Repository]
    _repo_by_name: dict[str, Repository]

    def __init__(self, repositories_config: YamlConfig) -> None:
        self._repositories = []
        self._repo_by_name = {}

        # process source loops
        for repodata in repositories_config.get_items():
            extra_groups = set()

            processed_sources = []
            for source in repodata['sources']:
                if source.get('disabled', False):
                    continue

                names = source['name'] if isinstance(source['name'], list) else [source['name']]
                for name in names:
                    processed_source = copy.deepcopy(source)
                    processed_source['name'] = name
                    _subst_source_recursively(processed_source, name)
                    processed_sources.append(processed_source)

                extra_groups.add(source['fetcher']['class'])
                extra_groups.add(source['parser']['class'])

            repo = Repository(
                name=repodata['name'],
                sortname=repodata.get('sortname', repodata['name']),
                singular=repodata.get('singular', repodata['desc'] + ' package'),
                type=repodata.get('type', 'repository'),
                desc=repodata['desc'],
                statsgroup=repodata.get('statsgroup', repodata['desc']),
                family=repodata['family'],
                ruleset=_listify(repodata.get('ruleset', repodata['family'])),
                color=repodata.get('color', '000000'),
                valid_till=str(repodata.get('valid_till')),
                default_maintainer=repodata.get('default_maintainer'),
                update_period=_parse_duration(repodata.get('update_period', 600)),
                minpackages=repodata.get('minpackages', 0),

                shadow=repodata.get('shadow', False),
                incomplete=repodata.get('incomplete', False),

                repolinks=repodata.get('repolinks', []),
                packagelinks=repodata.get('packagelinks', []),

                groups=repodata.get('groups', []) + list(extra_groups),

                sources=processed_sources,
            )

            self._repositories.append(repo)
            self._repo_by_name[repo.name] = repo

        self._repositories = sorted(self._repositories, key=lambda repo: repo.sortname)

    def get_repository(self, reponame: str) -> Repository:
        return self._repo_by_name[reponame]

    def get_repositories(self, reponames: RepositoryNameList = None) -> list[Repository]:
        if reponames is None:
            return []

        filtered_repositories = []

        for repository in self._repositories:
            for reponame in reponames:
                if reponame == repository.name or reponame in repository.groups:
                    filtered_repositories.append(repository)
                    break

        return filtered_repositories

    def get_names(self, reponames: RepositoryNameList = None) -> list[str]:
        return [repository.name for repository in self.get_repositories(reponames)]

    def get_metadatas(self, reponames: RepositoryNameList = None) -> list[RepositoryMetadata]:
        # TODO: remove this, just output all the keys
        keys = [
            'name',
            'sortname',
            'shadow',
            'incomplete',
            'repolinks',
            'packagelinks',
            'family',
            'desc',
            'singular',
            'type',
            'color',
            'statsgroup',
            'update_period',
        ]

        return [
            {
                key: repository.__dict__[key] for key in keys
            } for repository in self.get_repositories(reponames)
        ]
