# Copyright (C) 2016-2021, 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import datetime
import json
import warnings
from enum import Enum
from typing import Any, Collection, Optional, TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder

from repology.package import LinkType
from repology.yamlloader import YamlConfig


RepositoryNameList = Optional[Collection[str]]  # XXX: can't use |-union yet, see https://github.com/python/mypy/issues/11280


T = TypeVar('T')


def _subst_source_recursively(data: T, name: str) -> T:
    if isinstance(data, str):
        if '{source}' in data:
            warnings.warn('{source} substitution in repo config', DeprecationWarning)
        return data.replace('{source}', name)  # type: ignore
    elif isinstance(data, list):
        return [_subst_source_recursively(item, name) for item in data]  # type: ignore
    elif isinstance(data, dict):
        return {key: _subst_source_recursively(value, name) for key, value in data.items()}  # type: ignore
    else:
        return data


@overload
def _parse_duration(arg: str | int) -> datetime.timedelta:
    pass


@overload
def _parse_duration(arg: None) -> None:
    pass


def _parse_duration(arg: str | int | None) -> datetime.timedelta | None:
    if arg is None:
        return None
    if isinstance(arg, int):
        return datetime.timedelta(seconds=arg)
    elif arg.endswith('m'):
        return datetime.timedelta(minutes=int(arg[:-1]))
    elif arg.endswith('h'):
        return datetime.timedelta(hours=int(arg[:-1]))
    elif arg.endswith('d'):
        return datetime.timedelta(days=int(arg[:-1]))
    else:
        return datetime.timedelta(seconds=int(arg))


def _listify(arg: Any) -> list[Any]:
    if not isinstance(arg, list):
        return [arg]
    else:
        return arg


@dataclass
class PackageLink:
    type: int  # noqa
    url: str
    priority: int = 1


@dataclass
class Source:
    name: str

    subrepo: Optional[str]

    fetcher: dict[str, Any]
    parser: dict[str, Any]

    packagelinks: list[PackageLink]


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
    color: Optional[str]
    valid_till: Optional[datetime.date]
    default_maintainer: Optional[str]
    update_period: datetime.timedelta
    minpackages: int

    shadow: bool
    incomplete: bool

    repolinks: list[Any]
    packagelinks: list[PackageLink]

    groups: list[str]

    sources: list[Source]


class RepositoryManager:
    _repositories: list[Repository]
    _repo_by_name: dict[str, Repository]

    def __init__(self, repositories_config: YamlConfig) -> None:
        self._repositories = []
        self._repo_by_name = {}

        # process source loops
        for repodata in repositories_config.get_items():
            extra_groups = set()

            sources = []
            for sourcedata in repodata['sources']:
                if sourcedata.get('disabled', False):
                    continue

                for name in _listify(sourcedata['name']):
                    # if there are multiple names, clone source data for each of them
                    processed_sourcedata = _subst_source_recursively(copy.deepcopy(sourcedata), name)
                    sources.append(
                        Source(
                            name=name,
                            subrepo=processed_sourcedata.get('subrepo'),
                            fetcher=processed_sourcedata['fetcher'],
                            parser=processed_sourcedata['parser'],
                            packagelinks=[
                                PackageLink(
                                    type=LinkType.from_string(linkdata['type']),
                                    url=linkdata['url'],
                                    priority=linkdata.get('priority', 1),
                                )
                                for linkdata in processed_sourcedata.get('packagelinks', [])],
                        )
                    )

                extra_groups.add(sourcedata['fetcher']['class'])
                extra_groups.add(sourcedata['parser']['class'])

            repo = Repository(
                name=repodata['name'],
                sortname=repodata.get('sortname', repodata['name']),
                singular=repodata.get('singular', repodata['desc'] + ' package'),
                type=repodata.get('type', 'repository'),
                desc=repodata['desc'],
                statsgroup=repodata.get('statsgroup', repodata['desc']),
                family=repodata['family'],
                ruleset=_listify(repodata.get('ruleset', repodata['family'])),
                color=repodata.get('color'),
                valid_till=repodata.get('valid_till'),
                default_maintainer=repodata.get('default_maintainer'),
                update_period=_parse_duration(repodata.get('update_period', 600)),
                minpackages=repodata.get('minpackages', 0),

                shadow=repodata.get('shadow', False),
                incomplete=repodata.get('incomplete', False),

                repolinks=repodata.get('repolinks', []),
                packagelinks=[
                    PackageLink(
                        type=LinkType.from_string(linkdata['type']),
                        url=linkdata['url'],
                        priority=linkdata.get('priority', 1),
                    )
                    for linkdata in repodata.get('packagelinks', [])
                ],

                groups=repodata.get('groups', []) + list(extra_groups),

                sources=sources,
            )

            self._repositories.append(repo)
            self._repo_by_name[repo.name] = repo

        self._repositories = sorted(self._repositories, key=lambda repo: repo.sortname)

    def get_repository(self, name: str) -> Repository:
        return self._repo_by_name[name]

    def get_repositories(self, names: RepositoryNameList = None) -> list[Repository]:
        if names is None:
            return []

        filtered_repositories = []

        for repository in self._repositories:
            for name in names:
                if name == repository.name or name in repository.groups:
                    filtered_repositories.append(repository)
                    break

        return filtered_repositories

    def get_names(self, names: RepositoryNameList = None) -> list[str]:
        return [repository.name for repository in self.get_repositories(names)]

    def get_repository_json(self, name: str) -> str:
        return json.dumps(self.get_repository(name), default=pydantic_encoder)
