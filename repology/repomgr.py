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

import os
from typing import List, Optional

import yaml


class RepositoryManager:
    def __init__(self, reposdir=None, repostext=None):
        self.repositories = []
        self.repo_by_name = {}

        if repostext:
            self.repositories = yaml.safe_load(repostext)
        else:
            for root, dirs, files in os.walk(reposdir):
                for filename in filter(lambda f: f.endswith('.yaml'), files):
                    with open(os.path.join(root, filename)) as reposfile:
                        self.repositories += yaml.safe_load(reposfile)

        # process source loops
        for repo in self.repositories:
            newsources = []
            for source in repo['sources']:
                names = source['name'] if isinstance(source['name'], list) else [source['name']]
                for name in names:
                    newsource = source.copy()
                    for key in newsource.keys():
                        if isinstance(newsource[key], str):
                            newsource[key] = newsource[key].replace('{source}', name)
                    newsource['name'] = name
                    newsources.append(newsource)

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

            repo['ruleset'] = set(repo['ruleset'])

            self.repo_by_name[repo['name']] = repo

    def GetRepository(self, reponame):
        return self.repo_by_name[reponame]

    def GetRepositories(self, reponames=None):
        if reponames is None:
            return []

        filtered_repositories = []
        for repository in self.repositories:
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

    def GetNames(self, reponames: Optional[List[str]] = None) -> List[str]:
        return [repo['name'] for repo in sorted(self.GetRepositories(reponames), key=lambda repo: repo['sortname'])]

    def GetMetadata(self, reponames=None):
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
            } for repository in self.GetRepositories(reponames)
        }

    def GetMetadatas(self, reponames=None):
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
            } for repository in self.GetRepositories(reponames)
        ]
