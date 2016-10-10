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
    def __init__(self, statedir, enable_shadow=True, logger=NoopLogger()):
        self.statedir = statedir
        self.enable_shadow = enable_shadow
        self.logger = logger

    def GetStatePath(self, repository):
        return os.path.join(self.statedir, repository['name'] + ".state")

    def GetSerializedPath(self, repository, tmp=False):
        tmpext = ".tmp" if tmp else ""
        return os.path.join(self.statedir, repository['name'] + ".packages" + tmpext)

    def ForEach(self, processor, tags=None, repositories=None):
        for repository in REPOSITORIES:
            if repositories and not repository['name'] in repositories:
                continue

            skip = False
            if tags:
                for tagset in tags:
                    skip = True
                    for tag in tagset if type(tagset) is list else [tagset]:
                        if tag in repository['tags']:
                            skip = False
                            break
                    if skip:
                        break

            if not skip:
                processor(repository)

    def GetNames(self, tags=None, repositories=None):
        names = []

        def AppendName(repository):
            names.append(repository['name'])

        self.ForEach(AppendName, tags=tags, repositories=repositories)

        return names

    def GetMetadata(self):
        return {repository['name']: {
            'incomplete': repository.get('incomplete', False),
            'shadow': repository.get('shadow', False),
            'link': repository.get('link', '#'),
            'repotype': repository['repotype'],
        } for repository in REPOSITORIES}

    def Fetch(self, update=True, tags=None, repositories=None):
        def Fetcher(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("fetching started")
            repository['fetcher'].Fetch(self.GetStatePath(repository), update=update, logger=logger)
            logger.Log("fetching complete")

        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        self.ForEach(Fetcher, tags, repositories)

    def Mix(self, packages_by_repo, name_transformer):
        packages = {}

        for repository in REPOSITORIES:
            reponame = repository['name']
            if reponame not in packages_by_repo:
                continue

            for package in packages_by_repo[reponame]:
                package.repotype = repository['repotype']  # XXX: hack
                metaname = name_transformer.TransformName(package, repository['repotype'])

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

    def Parse(self, name_transformer, tags=None, repositories=None):
        packages_by_repo = {}

        def Parser(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("parsing started")
            repo_packages = repository['parser'].Parse(self.GetStatePath(repository))
            packages_by_repo[repository['name']] = repo_packages
            logger.Log("parsing complete, {} packages".format(len(repo_packages)))

        self.ForEach(Parser, tags, repositories)

        self.logger.Log("merging started")
        packages = self.Mix(packages_by_repo, name_transformer)
        self.logger.Log("merging complete, {} metapackages".format(len(packages)))
        return packages

    def ParseAndSerialize(self, tags=None, repositories=None):
        def ParserSerializer(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("parsing + saving started")
            repo_packages = repository['parser'].Parse(self.GetStatePath(repository))
            pickle.dump(
                repo_packages,
                open(self.GetSerializedPath(repository, tmp=True), "wb")
            )
            os.rename(self.GetSerializedPath(repository, tmp=True), self.GetSerializedPath(repository))
            logger.Log("parsing + saving complete, {} packages".format(len(repo_packages)))

        self.ForEach(ParserSerializer, tags, repositories)

    def Deserialize(self, name_transformer, tags=None, repositories=None):
        packages_by_repo = {}

        def Deserializer(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("loading started")
            repo_packages = pickle.load(open(self.GetSerializedPath(repository), "rb"))
            packages_by_repo[repository['name']] = repo_packages
            logger.Log("loading complete, {} packages".format(len(repo_packages)))

        self.ForEach(Deserializer, tags, repositories)

        self.logger.Log("merging started")
        packages = self.Mix(packages_by_repo, name_transformer)
        self.logger.Log("merging complete, {} metapackages".format(len(packages)))
        return packages
