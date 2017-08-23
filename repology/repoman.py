# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import datetime
import inspect
import os
import pickle
import sys
import time
import traceback

import yaml

from repology.fetcher import *
from repology.logger import NoopLogger
from repology.package import PackageSanityCheckFailure, PackageSanityCheckProblem
from repology.packageproc import PackagesMerge
from repology.parser import *


class StateFileFormatCheckProblem(Exception):
    def __init__(self, where):
        Exception.__init__(self, 'Illegal package format in {}. Please run `repology-update.py --parse` on all repositories to update the format.'.format(where))


class RepositoryManager:
    def __init__(self, reposdir, statedir, fetch_retries=3, fetch_retry_delay=30):
        self.repositories = []

        for root, dirs, files in os.walk(reposdir):
            for filename in filter(lambda f: f.endswith('.yaml'), files):
                with open(os.path.join(root, filename)) as reposfile:
                    self.repositories += yaml.safe_load(reposfile)

        # process source loops
        for repo in self.repositories:
            newsources = []
            for source in repo['sources']:
                if isinstance(source['name'], list):
                    for name in source['name']:
                        newsource = source.copy()
                        for key in newsource.keys():
                            if isinstance(newsource[key], str):
                                newsource[key] = newsource[key].replace('{source}', name)
                        newsource['name'] = name
                        newsources.append(newsource)
                else:
                    newsources.append(source)
            repo['sources'] = newsources

        self.statedir = statedir
        self.fetch_retries = fetch_retries
        self.fetch_retry_delay = fetch_retry_delay

    def __GetRepoPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.state')

    def __GetSourcePath(self, repository, source):
        return os.path.join(self.__GetRepoPath(repository), source['name'].replace('/', '_'))

    def __GetSerializedPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.packages')

    def __GetRepository(self, reponame):
        for repository in self.repositories:
            if repository['name'] == reponame:
                return repository

        raise KeyError('No such repository ' + reponame)

    def __CheckRepositoryOutdatedness(self, repository, logger):
        if 'valid_till' in repository and datetime.date.today() >= repository['valid_till']:
            logger.Log('WARNING: Repository {} has reached EoL, please update configs'.format(repository['name']))

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
        if 'fetcher' not in source:
            logger.Log('fetching source {} not supported'.format(source['name']))
            return

        fetcher = self.__SpawnClass(
            'Fetcher',
            source['fetcher'],
            source
        )

        ntry = 1
        while ntry <= self.fetch_retries:
            logger.Log('fetching source {} try {} started'.format(source['name'], ntry))

            try:
                fetcher.Fetch(
                    self.__GetSourcePath(repository, source),
                    update=update,
                    logger=logger.GetIndented()
                )

                break
            except KeyboardInterrupt:
                raise
            except:
                if ntry >= self.fetch_retries:
                    raise

                logger.Log('fetching source {} try {} failed:'.format(source['name'], ntry))
                for item in traceback.format_exception(*sys.exc_info()):
                    for line in item.split('\n'):
                        if line:
                            logger.GetIndented().Log(line)

                logger.Log('waiting {} seconds before retry'.format(self.fetch_retry_delay))
                if self.fetch_retry_delay:
                    time.sleep(self.fetch_retry_delay)

            ntry += 1

        logger.Log('fetching source {} complete with {} tries'.format(source['name'], ntry))

    def __ParseSource(self, repository, source, logger):
        if 'parser' not in source:
            logger.Log('parsing source {} not supported'.format(source['name']))
            return []

        logger.Log('parsing source {} started'.format(source['name']))

        # parse
        packages = self.__SpawnClass(
            'Parser',
            source['parser'],
            source
        ).Parse(
            self.__GetSourcePath(repository, source)
        )

        logger.Log('parsing source {} postprocessing'.format(source['name']))

        for package in packages:
            # - fill subrepos
            if 'subrepo' in source:
                package.subrepo = source['subrepo']

            # - fill default maintainer
            if not package.maintainers:
                if 'default_maintainer' in repository:
                    package.maintainers = [repository['default_maintainer']]
                else:
                    package.maintainers = ['fallback-mnt-{}@repology'.format(repository['name'])]

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

        logger.Log('parsing complete, {} packages, merging'.format(len(packages)))

        packages = PackagesMerge(packages)

        logger.Log('merging complete, {} packages'.format(len(packages)))

        return packages

    def __Transform(self, packages, transformer, repository, logger):
        logger.Log('processing started')
        sanitylogger = logger.GetIndented()
        for package in packages:
            package.repo = repository['name']
            package.family = repository['family']
            if 'shadow' in repository and repository['shadow']:
                package.shadow = True
            if transformer:
                transformer.Process(package)

            try:
                package.CheckSanity(transformed=transformer is not None)
            except PackageSanityCheckFailure as err:
                sanitylogger.Log('sanity error: {}'.format(err))
                raise
            except PackageSanityCheckProblem as err:
                sanitylogger.Log('sanity warning: {}'.format(err))

            package.Normalize()

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
        os.replace(tmppath, path)
        logger.Log('saving complete, {} packages'.format(len(packages)))

    def __Deserialize(self, path, repository, logger):
        packages = []
        logger.Log('loading started')
        with open(path, 'rb') as infile:
            unpickler = pickle.Unpickler(infile)
            numpackages = unpickler.load()
            packages = [unpickler.load() for num in range(0, numpackages)]
            if packages and not packages[0].CheckFormat():
                raise StateFileFormatCheckProblem(path)
        logger.Log('loading complete, {} packages'.format(len(packages)))

        return packages

    class __StreamDeserializer:
        def __init__(self, path):
            self.unpickler = pickle.Unpickler(open(path, 'rb'))
            self.count = self.unpickler.load()
            self.current = None

            self.Get()

            if self.current and not self.current.CheckFormat():
                raise StateFileFormatCheckProblem(path)

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

    def GetMetadata(self, reponames=None):
        return {
            repository['name']: {
                'incomplete': repository.get('incomplete', False),
                'shadow': repository.get('shadow', False),
                'repolinks': repository.get('repolinks', []),
                'packagelinks': repository.get('packagelinks', []),
                'family': repository['family'],
                'desc': repository['desc'],
                'type': repository['type'],
                'color': repository.get('color'),
            } for repository in self.__GetRepositories(reponames)
        }

    # Single repo methods
    def Fetch(self, reponame, update=True, logger=NoopLogger()):
        repository = self.__GetRepository(reponame)

        self.__CheckRepositoryOutdatedness(repository, logger)

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

        while True:
            # remove EOFed repos
            deserializers = [ds for ds in deserializers if not ds.EOF()]

            # stop when all deserializers are empty
            if not deserializers:
                break

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
