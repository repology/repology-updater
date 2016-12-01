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

    # Single repo methods
    def Fetch(self, reponame, update=True, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("fetching started")
        repository['fetcher'].Fetch(self.GetStatePath(repository), update=update, logger=logger.GetIndented())
        logger.Log("fetching complete")

    def Parse(self, reponame, transformer=None, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("parsing started")
        packages = repository['parser'].Parse(self.GetStatePath(repository))
        logger.Log("parsing complete, {} packages".format(len(packages)))

        logger.Log("processing started")
        for package in packages:
            package.repo = reponame
            package.family = repository['family']
            if 'shadow' in repository and repository['shadow']:
                package.shadow = True
            if transformer:
                transformer.Process(package)
        logger.Log("processing complete, {} packages".format(len(packages)))

        # XXX: later, we'll pass ignored packages; they will still
        # be ignored in summary calculations, but will be visible
        # in packages list
        return [ package for package in packages if not package.ignore ]

    def ParseAndSerialize(self, reponame, transformer=None, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        packages = self.Parse(reponame, transformer, logger)

        logger.Log("saving started")
        pickle.dump(
            packages,
            open(self.GetSerializedPath(repository, tmp=True), "wb")
        )
        os.rename(self.GetSerializedPath(repository, tmp=True), self.GetSerializedPath(repository))
        logger.Log("saving complete, {} packages".format(len(packages)))

        return packages

    def Deserialize(self, reponame, transformer=None, logger=NoopLogger()):
        repository = self.GetRepository(reponame)

        logger.Log("loading started")
        packages = pickle.load(open(self.GetSerializedPath(repository), "rb"))
        logger.Log("loading complete, {} packages".format(len(packages)))

        if transformer:
            logger.Log("processing started")
            for package in packages:
                transformer.Process(package)
            logger.Log("processing complete, {} packages".format(len(packages)))

        return packages

    # Multi repo methods
    def FetchMulti(self, update=True, reponames=None, logger=NoopLogger()):
        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        for repo in self.GetRepositories(reponames):
            self.Fetch(repo['name'], update=update, logger=logger.GetPrefixed(repo['name'] + ": "))

    def ParseMulti(self, reponames=None, transformer=None, logger=NoopLogger()):
        packages = []

        for repo in self.GetRepositories(reponames):
            packages += self.Parse(repo['name'], transformer=transformer, logger=logger.GetPrefixed(repo['name'] + ": "))

        return packages

    def ParseAndSerializeMulti(self, reponames=None, transformer=None, logger=NoopLogger()):
        for repo in self.GetRepositories(reponames):
            self.ParseAndSerialize(repo['name'], transformer=transformer, logger=logger.GetPrefixed(repo['name'] + ": "))

    def DeserializeMulti(self, reponames=None, transformer=None, logger=NoopLogger()):
        packages = []

        for repo in self.GetRepositories(reponames):
            packages += self.Deserialize(repo['name'], transformer=transformer, logger=logger.GetPrefixed(repo['name'] + ": "))

        return packages
