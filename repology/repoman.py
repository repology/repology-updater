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
from repology.logger import NoopLogger
from repology.repositories import REPOSITORIES


class RepositoryManager:
    def __init__(self, statedir, enable_shadow=True):
        self.statedir = statedir
        self.enable_shadow = enable_shadow

    def __GetStatePath(self, repository):
        return os.path.join(self.statedir, repository['name'] + ".state")

    def __GetSerializedPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + ".packages")

    def __GetRepository(self, reponame):
        for repository in REPOSITORIES:
            if repository['name'] == reponame:
                return repository

        raise KeyError('No such repository ' + reponame)

    def __GetRepositories(self, reponames=None):
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

    # Private methods which provide single actions on repos
    def __Fetch(self, update, repository, logger):
        logger.Log("fetching started")
        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        repository['fetcher'].Fetch(self.__GetStatePath(repository), update=update, logger=logger.GetIndented())
        logger.Log("fetching complete")

    def __Parse(self, repository, logger):
        logger.Log("parsing started")
        packages = repository['parser'].Parse(self.__GetStatePath(repository))
        logger.Log("parsing complete, {} packages".format(len(packages)))

        return packages

    def __Transform(self, packages, transformer, repository, logger):
        logger.Log("processing started")
        for package in packages:
            package.repo = repository['name']
            package.family = repository['family']
            if 'shadow' in repository and repository['shadow']:
                package.shadow = True
            if transformer:
                transformer.Process(package)

        # XXX: in future, ignored packages will not be dropped here, but
        # ignored in summary and version calcualtions, but shown in
        # package listing
        packages = [ package for package in packages if not package.ignore ]
        logger.Log("processing complete, {} packages".format(len(packages)))

        return packages

    def __Serialize(self, packages, path, repository, logger):
        tmppath = path + ".tmp"

        logger.Log("saving started")
        pickle.dump(packages, open(tmppath, "wb"))
        os.rename(tmppath, path)
        logger.Log("saving complete, {} packages".format(len(packages)))

    def __Deserialize(self, path, repository, logger):
        logger.Log("loading started")
        packages = pickle.load(open(path, "rb"))
        logger.Log("loading complete, {} packages".format(len(packages)))

        return packages

    # Helpers to retrieve data on repositories
    def GetNames(self, reponames=None):
        return [repo['name'] for repo in self.__GetRepositories(reponames)]

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
        repository = self.__GetRepository(reponame)

        self.__Fetch(update, repository, logger)

    def Parse(self, reponame, transformer, logger=NoopLogger()):
        repository = self.__GetRepository(reponame)

        packages = self.__Parse(repository, logger)
        packages = self.__Transform(packages, transformer, repository, logger)

        return packages

    def ParseAndSerialize(self, reponame, transformer, logger=NoopLogger()):
        repository = self.__GetRepository(reponame)

        packages = self.__Parse(repository, logger)
        packages = self.__Transform(packages, transformer, repository, logger)
        self.__Serialize(packages, self.__GetSerializedPath(repository), repository, logger)

        return packages

    def Deserialize(self, reponame, logger=NoopLogger()):
        repository = self.__GetRepository(reponame)

        return self.__Deserialize(self.__GetSerializedPath(repository), repository, logger)

    def Reprocess(self, reponame, transformer=None, logger=NoopLogger()):
        repository = self.__GetRepository(reponame)

        packages = self.__Deserialize(self.__GetSerializedPath(repository), repository, logger)
        packages = self.__Transform(packages, transformer, repository, logger)
        self.__Serialize(packages, self.__GetSerializedPath(repository), repository, logger)

        return packages

    # Multi repo methods
    def ParseMulti(self, reponames=None, transformer=None, logger=NoopLogger()):
        packages = []

        for repo in self.__GetRepositories(reponames):
            packages += self.Parse(repo['name'], transformer=transformer, logger=logger.GetPrefixed(repo['name'] + ": "))

        return packages

    def DeserializeMulti(self, reponames=None, transformer=None, logger=NoopLogger()):
        packages = []

        for repo in self.__GetRepositories(reponames):
            packages += self.Deserialize(repo['name'], logger=logger.GetPrefixed(repo['name'] + ": "))

        return packages
