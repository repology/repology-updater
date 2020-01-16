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

import os
from typing import Any, Collection, Dict, List, Optional

import yaml


RepositoryNameList = Optional[Collection[str]]
RepositoryMetadata = Dict[str, Any]


class RepositoryManager:
    _repositories: List[RepositoryMetadata]
    _repo_by_name: Dict[str, RepositoryMetadata]

    def __init__(self, reposdir: Optional[str] = None, repostext: Optional[str] = None) -> None:
        self._repositories = []
        self._repo_by_name = {}

        if isinstance(repostext, str):
            self._repositories = yaml.safe_load(repostext)
        elif isinstance(reposdir, str):
            for root, dirs, files in os.walk(reposdir):
                for filename in filter(lambda f: f.endswith('.yaml'), files):
                    with open(os.path.join(root, filename)) as reposfile:
                        self._repositories += yaml.safe_load(reposfile)
        else:
            raise RuntimeError('rulesdir or rulestext must be defined')

        # process source loops
        for repo in self._repositories:
            extratags = set()

            newsources = []
            for source in repo['sources']:
                if source.get('disabled', False):
                    continue

                names = source['name'] if isinstance(source['name'], list) else [source['name']]
                for name in names:
                    newsource = source.copy()
                    for key in newsource.keys():
                        if isinstance(newsource[key], str):
                            newsource[key] = newsource[key].replace('{source}', name)
                    newsource['name'] = name
                    newsources.append(newsource)

                extratags.add(source['fetcher'])
                extratags.add(source['parser'])

            repo['sources'] = newsources

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

            repo['tags'] += list(extratags)

            self._repo_by_name[repo['name']] = repo

    def get_repository(self, reponame: str) -> RepositoryMetadata:
        return self._repo_by_name[reponame]

    def get_repositories(self, reponames: RepositoryNameList = None) -> List[RepositoryMetadata]:
        if reponames is None:
            return []

        filtered_repositories = []
        for repository in self._repositories:
            match = False
            for reponame in reponames:
                if reponame == repository['name']:
                    match = True
                    break
                if reponame in repository['tags']:
                    match = True
                    break
            if match:
                filtered_repositories.append(repository)

        return filtered_repositories

    def get_names(self, reponames: RepositoryNameList = None) -> List[str]:
        return [repo['name'] for repo in sorted(self.get_repositories(reponames), key=lambda repo: repo['sortname'])]

    def get_metadata(self, reponames: RepositoryNameList = None) -> Dict[str, RepositoryMetadata]:
        return {
            repository['name']: {
                'shadow': repository.get('shadow', False),
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

    def get_metadatas(self, reponames: RepositoryNameList = None) -> List[RepositoryMetadata]:
        return [
            {
                'name': repository['name'],
                'sortname': repository['sortname'],
                'shadow': repository.get('shadow', False),
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
