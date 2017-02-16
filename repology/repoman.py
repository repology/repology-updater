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

import inspect
import os
import pickle

import yaml

from repology.fetcher import *
from repology.logger import NoopLogger
from repology.parser import *


class RepositoryManager:
    def __init__(self, repospath, statedir):
        with open(repospath) as reposfile:
            self.repositories = yaml.safe_load(reposfile)
        self.statedir = statedir

    def __GetRepoPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.state')

    def __GetSourcePath(self, repository, source):
        return os.path.join(self.__GetRepoPath(repository), source['name'])

    def __GetSerializedPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.packages')

    def __GetRepository(self, reponame):
        for repository in self.repositories:
            if repository['name'] == reponame:
                return repository

        raise KeyError('No such repository ' + reponame)

    def __GetRepositories(self, reponames=None):
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

    # Parser/fetcher factory
    def __SpawnClass(self, suffix, name, argsdict):
        spawned_name = name + suffix
        if spawned_name not in globals():
            raise RuntimeError('unknown {} {}'.format(suffix.lower(), name))

        spawned_class = globals()[spawned_name]
        spawned_argspec = inspect.getfullargspec(spawned_class.__init__)
        spawned_args = {
            key: value for key, value in argsdict.items() if key in spawned_argspec.args
        }

        return spawned_class(**spawned_args)

    # Private methods which provide single actions on sources
    def __FetchSource(self, update, repository, source, logger):
        logger.Log('fetching source {} started'.format(source['name']))

        self.__SpawnClass(
            'Fetcher',
            source['fetcher'],
            source
        ).Fetch(
            self.__GetSourcePath(repository, source),
            update=update,
            logger=logger.GetIndented()
        )

        logger.Log('fetching source {} complete'.format(source['name']))

    def __ParseSource(self, repository, source, logger):
        logger.Log('parsing source {} started'.format(source['name']))

        packages = self.__SpawnClass(
            'Parser',
            source['parser'],
            source
        ).Parse(
            self.__GetSourcePath(repository, source)
        )

        logger.Log('parsing source {} complete'.format(source['name']))

        return packages

    # Private methods which provide single actions on repos
    def __Fetch(self, update, repository, logger):
        logger.Log('fetching started')

        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        for source in repository['sources']:
            if not os.path.isdir(self.__GetRepoPath(repository)):
                os.mkdir(self.__GetRepoPath(repository))
            self.__FetchSource(update, repository, source, logger.GetIndented())

        logger.Log('fetching complete')

    def __Parse(self, repository, logger):
        packages = []
        logger.Log('parsing started')

        for source in repository['sources']:
            packages += self.__ParseSource(repository, source, logger.GetIndented())

        logger.Log('parsing complete, {} packages'.format(len(packages)))

        return packages

    def __Transform(self, packages, transformer, repository, logger):
        logger.Log('processing started')
        for package in packages:
            package.repo = repository['name']
            package.family = repository['family']
            if 'shadow' in repository and repository['shadow']:
                package.shadow = True
            if transformer:
                transformer.Process(package)

        if transformer:
            packages = sorted(packages, key=lambda package: package.effname)

        # XXX: in future, ignored packages will not be dropped here, but
        # ignored in summary and version calcualtions, but shown in
        # package listing
        packages = [package for package in packages if not package.ignore]
        logger.Log('processing complete, {} packages'.format(len(packages)))

        return packages

    def __Serialize(self, packages, path, repository, logger):
        tmppath = path + '.tmp'

        logger.Log('saving started')
        with open(tmppath, 'wb') as outfile:
            pickler = pickle.Pickler(outfile, protocol=pickle.HIGHEST_PROTOCOL)
            pickler.fast = True  # deprecated, but I don't see any alternatives
            pickler.dump(len(packages))
            for package in packages:
                pickler.dump(package)
        os.rename(tmppath, path)
        logger.Log('saving complete, {} packages'.format(len(packages)))

    def __Deserialize(self, path, repository, logger):
        packages = []
        logger.Log('loading started')
        with open(path, 'rb') as infile:
            unpickler = pickle.Unpickler(infile)
            numpackages = unpickler.load()
            packages = [unpickler.load() for num in range(0, numpackages)]
        logger.Log('loading complete, {} packages'.format(len(packages)))

        return packages

    class __StreamDeserializer:
        def __init__(self, path):
            self.unpickler = pickle.Unpickler(open(path, 'rb'))
            self.count = self.unpickler.load()
            self.current = None

            self.Get()

        def Peek(self):
            return self.current

        def EOF(self):
            return self.current is None

        def Get(self):
            current = self.current
            if self.count == 0:
                self.current = None
            else:
                self.current = self.unpickler.load()
                self.count -= 1
            return current

    # Helpers to retrieve data on repositories
    def GetNames(self, reponames=None):
        return sorted([repo['name'] for repo in self.__GetRepositories(reponames)])

    def GetMetadata(self):
        return {repository['name']: {
            'incomplete': repository.get('incomplete', False),
            'shadow': repository.get('shadow', False),
            'url': repository.get('url'),
            'links': repository.get('links', []),
            'family': repository['family'],
            'desc': repository['desc'],
        } for repository in self.repositories}

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
            packages += self.Parse(repo['name'], transformer=transformer, logger=logger.GetPrefixed(repo['name'] + ': '))

        return packages

    def DeserializeMulti(self, reponames=None, logger=NoopLogger()):
        packages = []

        for repo in self.__GetRepositories(reponames):
            packages += self.Deserialize(repo['name'], logger=logger.GetPrefixed(repo['name'] + ': '))

        return packages

    def StreamDeserializeMulti(self, processor, reponames=None, logger=NoopLogger()):
        deserializers = []
        for repo in self.__GetRepositories(reponames):
            deserializers.append(self.__StreamDeserializer(self.__GetSerializedPath(repo)))

        while deserializers:
            # find lowest key (effname)
            thiskey = deserializers[0].Peek().effname
            for ds in deserializers[1:]:
                thiskey = min(thiskey, ds.Peek().effname)

            # fetch all packages with given key from all deserializers
            packageset = []
            for ds in deserializers:
                while not ds.EOF() and ds.Peek().effname == thiskey:
                    packageset.append(ds.Get())

            processor(packageset)

            # remove EOFed repos
            deserializers = [ds for ds in deserializers if not ds.EOF()]
