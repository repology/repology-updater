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

import datetime
import os
import pickle
import sys
import time
import traceback

from repology.fetchers import Fetcher
from repology.logger import NoopLogger
from repology.moduleutils import ClassFactory
from repology.package import PackageFlags, PackageSanityCheckFailure, PackageSanityCheckProblem
from repology.packageproc import PackagesetDeduplicate
from repology.parsers import Parser
from repology.resourceusage import ResourceUsageMonitor


class StateFileFormatCheckProblem(Exception):
    def __init__(self, where):
        Exception.__init__(self, 'Illegal package format in {}. Please run `repology-update.py --parse` on all repositories to update the format.'.format(where))


class TooLittlePackages(Exception):
    def __init__(self, numpackages, minpackages):
        Exception.__init__(self, 'Unexpectedly small number of packages: {} when expected no less than {}'.format(numpackages, minpackages))


class InconsistentPackage(Exception):
    pass


class RepositoryProcessor:
    def __init__(self, repoman, statedir, fetch_retries=3, fetch_retry_delay=30, safety_checks=True):
        self.repoman = repoman
        self.statedir = statedir
        self.fetch_retries = fetch_retries
        self.fetch_retry_delay = fetch_retry_delay
        self.safety_checks = safety_checks

        self.fetcher_factory = ClassFactory('repology.fetchers.fetchers', superclass=Fetcher)
        self.parser_factory = ClassFactory('repology.parsers.parsers', superclass=Parser)

    def __GetRepoPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.state')

    def __GetSourcePath(self, repository, source):
        return os.path.join(self.__GetRepoPath(repository), source['name'].replace('/', '_'))

    def __GetSerializedPath(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.packages')

    def __CheckRepositoryOutdatedness(self, repository, logger):
        if 'valid_till' in repository and datetime.date.today() >= repository['valid_till']:
            logger.Log('WARNING: Repository {} has reached EoL, please update configs'.format(repository['name']))

    # Private methods which provide single actions on sources
    def __FetchSource(self, update, repository, source, logger):
        if 'fetcher' not in source:
            logger.Log('fetching source {} not supported'.format(source['name']))
            return

        fetcher = self.fetcher_factory.SpawnWithKnownArgs(source['fetcher'], source)

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

        usage = ResourceUsageMonitor()

        # parse
        packages = self.parser_factory.SpawnWithKnownArgs(
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

            if not package.name:
                raise InconsistentPackage('package with no name')

            if not package.version:
                # XXX: this currently fires on kdepim in dports; it's pretty fatal on
                # one hand, but shouldn't stop whole repo from updating on another. In
                # future, it should be logged as some kind of very serious repository
                # update error
                logger.Log('ERROR: package with empty version'.format(package.name))

        logger.Log('parsing source {} complete, resource usage: {}'.format(source['name'], usage.get_usage_str()))

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

        logger.Log('parsing complete, {} packages, deduplicating'.format(len(packages)))

        packages = PackagesetDeduplicate(packages)

        if self.safety_checks and len(packages) < repository['minpackages']:
            raise TooLittlePackages(len(packages), repository['minpackages'])

        logger.Log('parsing complete, {} packages'.format(len(packages)))

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

        # XXX: in future, ignored packages will not be dropped here, but
        # ignored in summary and version calcualtions, but shown in
        # package listing
        packages = [package for package in packages if not package.HasFlag(PackageFlags.remove)]

        logger.Log('processing complete, {} packages, deduplicating'.format(len(packages)))

        packages = PackagesetDeduplicate(packages)

        if transformer:
            logger.Log('processing complete, {} packages, sorting'.format(len(packages)))

            packages = sorted(packages, key=lambda package: package.effname)

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

    class StreamDeserializer:
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

    # Single repo methods
    def Fetch(self, reponame, update=True, logger=NoopLogger()):
        repository = self.repoman.GetRepository(reponame)

        self.__CheckRepositoryOutdatedness(repository, logger)

        self.__Fetch(update, repository, logger)

    def Parse(self, reponame, transformer, logger=NoopLogger()):
        repository = self.repoman.GetRepository(reponame)

        packages = self.__Parse(repository, logger)
        packages = self.__Transform(packages, transformer, repository, logger)

        return packages

    def ParseAndSerialize(self, reponame, transformer, logger=NoopLogger()):
        repository = self.repoman.GetRepository(reponame)

        packages = self.__Parse(repository, logger)
        packages = self.__Transform(packages, transformer, repository, logger)
        self.__Serialize(packages, self.__GetSerializedPath(repository), repository, logger)

        return packages

    def Deserialize(self, reponame, logger=NoopLogger()):
        repository = self.repoman.GetRepository(reponame)

        return self.__Deserialize(self.__GetSerializedPath(repository), repository, logger)

    def Reprocess(self, reponame, transformer=None, logger=NoopLogger()):
        repository = self.repoman.GetRepository(reponame)

        packages = self.__Deserialize(self.__GetSerializedPath(repository), repository, logger)
        packages = self.__Transform(packages, transformer, repository, logger)
        self.__Serialize(packages, self.__GetSerializedPath(repository), repository, logger)

        return packages

    # Multi repo methods
    def ParseMulti(self, reponames=None, transformer=None, logger=NoopLogger()):
        packages = []

        for repo in self.repoman.GetRepositories(reponames):
            packages += self.Parse(repo['name'], transformer=transformer, logger=logger.GetPrefixed(repo['name'] + ': '))

        return packages

    def DeserializeMulti(self, reponames=None, logger=NoopLogger()):
        packages = []

        for repo in self.repoman.GetRepositories(reponames):
            packages += self.Deserialize(repo['name'], logger=logger.GetPrefixed(repo['name'] + ': '))

        return packages

    def StreamDeserializeMulti(self, processor, reponames=None, logger=NoopLogger()):
        deserializers = []
        for repo in self.repoman.GetRepositories(reponames):
            deserializers.append(self.StreamDeserializer(self.__GetSerializedPath(repo)))

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
