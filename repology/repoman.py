#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import sys
import pickle
import fcntl

from repology.package import *
from repology.logger import *
from repology.repositories import REPOSITORIES


class RepositoryManager:
    def __init__(self, statedir, enable_shadow=True):
        self.statedir = statedir
        self.enable_shadow = enable_shadow

    def GetStatePath(self, repository):
        return os.path.join(self.statedir, repository['name'] + ".state")

    def GetSerializedPath(self, repository, tmp=False):
        tmpext = ".tmp" if tmp else ""
        return os.path.join(self.statedir, repository['name'] + ".packages" + tmpext)

    def GetRepository(self, reponame):
        for repository in REPOSITORIES:
            if repository['name'] == reponame:
                return repository

        raise KeyError('No such repository ' + reponame)

    def GetRepositories(self, reponames=None):
        if reponames is None:
            return []

        filtered_repositories = []
        for repository in REPOSITORIES:
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

    def ForEach(self, processor, reponames=None):
        for repo in self.GetRepositories(reponames):
            processor(repo)

    def GetNames(self, reponames=None):
        return [repo['name'] for repo in self.GetRepositories(reponames)]

    def GetMetadata(self):
        return {repository['name']: {
            'incomplete': repository.get('incomplete', False),
            'shadow': repository.get('shadow', False),
            'link': repository.get('link'),
            'family': repository['family'],
            'desc': repository['desc'],
        } for repository in REPOSITORIES}

    def Mix(self, packages_by_repo, name_transformer):
        packages = {}

        for repository in REPOSITORIES:
            reponame = repository['name']
            if reponame not in packages_by_repo:
                continue

            for package in packages_by_repo[reponame]:
                package.family = repository['family']  # XXX: hack
                metaname = name_transformer.TransformName(package)

                if metaname is None:
                    continue
                if metaname not in packages:
                    packages[metaname] = MetaPackage(metaname)
                packages[metaname].Add(reponame, package)

        for package in packages.values():
            package.FillVersionData()

        shadows = set()

        if self.enable_shadow:
            for repository in REPOSITORIES:
                if 'shadow' in repository and repository['shadow']:
                    shadows.add(repository['name'])

        def CheckShadows(package):
            for repo in package.versions.keys():
                if repo not in shadows:
                    return True

            return False

        return [packages[name] for name in sorted(packages.keys()) if CheckShadows(packages[name])]

    # Single repo methods
    def FetchOne(self, reponame, update=True, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("fetching started")
        repository['fetcher'].Fetch(self.GetStatePath(repository), update=update, logger=logger.GetIndented())
        logger.Log("fetching complete")

    def ParseOne(self, reponame, name_transformer, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("parsing started")
        repo_packages = repository['parser'].Parse(self.GetStatePath(repository))
        logger.Log("parsing complete, {} packages".format(len(repo_packages)))
        return repo_packages

    def ParseAndSerializeOne(self, reponame, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("parsing + saving started")
        repo_packages = repository['parser'].Parse(self.GetStatePath(repository))
        pickle.dump(
            repo_packages,
            open(self.GetSerializedPath(repository, tmp=True), "wb")
        )
        os.rename(self.GetSerializedPath(repository, tmp=True), self.GetSerializedPath(repository))
        logger.Log("parsing + saving complete, {} packages".format(len(repo_packages)))

    def DeserializeOne(self, reponame, name_transformer, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("loading started")
        repo_packages = pickle.load(open(self.GetSerializedPath(repository), "rb"))
        logger.Log("loading complete, {} packages".format(len(repo_packages)))
        return repo_packages

    # Multi repo methods
    def Fetch(self, update=True, reponames=None, logger=NoopLogger()):
        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        for repo in self.GetRepositories(reponames):
            self.FetchOne(repo['name'], update=update, logger=logger.GetPrefixed(repo['name'] + ": "))

    def Parse(self, name_transformer, reponames, logger=NoopLogger()):
        packages_by_repo = {}

        for repo in self.GetRepositories(reponames):
            packages_by_repo[repo['name']] = self.ParseOne(repo['name'], logger=logger.GetPrefixed(repo['name'] + ": "))

        logger.Log("merging started")
        packages = self.Mix(packages_by_repo, name_transformer)
        logger.Log("merging complete, {} metapackages".format(len(packages)))
        return packages

    def ParseAndSerialize(self, reponames=None, logger=NoopLogger()):
        for repo in self.GetRepositories(reponames):
            self.ParseAndSerializeOne(repo['name'], logger=logger.GetPrefixed(repo['name'] + ": "))

    def Deserialize(self, name_transformer, reponames=None, logger=NoopLogger()):
        packages_by_repo = {}

        for repo in self.GetRepositories(reponames):
            packages_by_repo[repo['name']] = self.DeserializeOne(repo['name'], name_transformer, logger=logger.GetPrefixed(repo['name'] + ": "))

        logger.Log("merging started")
        packages = self.Mix(packages_by_repo, name_transformer)
        logger.Log("merging complete, {} metapackages".format(len(packages)))
        return packages
