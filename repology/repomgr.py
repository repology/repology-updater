# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Collection, Iterable, Optional, cast

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


class RepositoryManager:
    _repositories: list[RepositoryMetadata]
    _repo_by_name: dict[str, RepositoryMetadata]

    def __init__(self, repositories_config: YamlConfig) -> None:
        self._repositories = repositories_config.get_items()
        self._repo_by_name = {}

        # process source loops
        for repo in self._repositories:
            extra_groups = set()

            processed_sources = []
            for source in repo['sources']:
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

            repo['sources'] = processed_sources

            if 'sortname' not in repo:
                repo['sortname'] = repo['name']

            if 'singular' not in repo:
                repo['singular'] = repo['desc'] + ' package'

            # XXX: legacy, ruleset will be required
            if 'ruleset' not in repo:
                repo['ruleset'] = [repo['family']]

            if not isinstance(repo['ruleset'], list):
                repo['ruleset'] = [repo['ruleset']]

            if 'minpackages' not in repo:
                repo['minpackages'] = 0

            if 'update_period' not in repo:
                repo['update_period'] = 600  # XXX: default update period - move to config?
            elif isinstance(repo['update_period'], str):
                if repo['update_period'].endswith('m'):
                    repo['update_period'] = int(repo['update_period'][:-1]) * 60
                elif repo['update_period'].endswith('h'):
                    repo['update_period'] = int(repo['update_period'][:-1]) * 60 * 60
                elif repo['update_period'].endswith('d'):
                    repo['update_period'] = int(repo['update_period'][:-1]) * 60 * 60 * 24
                else:
                    raise RuntimeError('unexpected update_period format')

            repo['ruleset'] = set(repo['ruleset'])

            repo.setdefault('groups', []).extend(extra_groups)

            self._repo_by_name[repo['name']] = repo

        def repo_sort_key(repo: RepositoryMetadata) -> str:
            assert isinstance(repo['sortname'], str)
            return repo['sortname']

        self._repositories = sorted(self._repositories, key=repo_sort_key)

    def get_repository(self, reponame: str) -> RepositoryMetadata:
        return self._repo_by_name[reponame]

    def get_repositories(self, reponames: RepositoryNameList = None) -> list[RepositoryMetadata]:
        if reponames is None:
            return []

        filtered_repositories = []
        for repository in self._repositories:
            match = False
            for reponame in reponames:
                if reponame == repository['name']:
                    match = True
                    break
                if reponame in repository['groups']:
                    match = True
                    break
            if match:
                filtered_repositories.append(repository)

        return filtered_repositories

    def get_names(self, reponames: RepositoryNameList = None) -> list[str]:
        return [repo['name'] for repo in sorted(self.get_repositories(reponames), key=lambda repo: cast(str, repo['sortname']))]

    def get_metadata(self, reponames: RepositoryNameList = None) -> dict[str, RepositoryMetadata]:
        return {
            repository['name']: {
                'shadow': repository.get('shadow', False),
                'incomplete': repository.get('incomplete', False),
                'repolinks': repository.get('repolinks', []),
                'packagelinks': repository.get('packagelinks', []),
                'family': repository['family'],
                'desc': repository['desc'],
                'singular': repository['singular'],
                'type': repository['type'],
                'color': repository.get('color'),
                'statsgroup': repository.get('statsgroup', repository['desc']),
                'update_period': repository['update_period'],
            } for repository in self.get_repositories(reponames)
        }

    def get_metadatas(self, reponames: RepositoryNameList = None) -> list[RepositoryMetadata]:
        return [
            {
                'name': repository['name'],
                'sortname': repository['sortname'],
                'shadow': repository.get('shadow', False),
                'incomplete': repository.get('incomplete', False),
                'repolinks': repository.get('repolinks', []),
                'packagelinks': repository.get('packagelinks', []),
                'family': repository['family'],
                'desc': repository['desc'],
                'singular': repository['singular'],
                'type': repository['type'],
                'color': repository.get('color'),
                'statsgroup': repository.get('statsgroup', repository['desc']),
                'update_period': repository['update_period'],
            } for repository in self.get_repositories(reponames)
        ]
