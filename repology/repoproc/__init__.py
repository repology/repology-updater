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

from repology.atomic_fs import AtomicDir
from repology.fetchers import Fetcher
from repology.logger import Logger, NoopLogger
from repology.moduleutils import ClassFactory
from repology.package import PackageFlags
from repology.packagemaker import PackageFactory
from repology.packageproc import PackagesetDeduplicate
from repology.parsers import Parser
from repology.repoproc.serialization import heap_deserializer, serialize


MAX_PACKAGES_PER_CHUNK = 10240


class StateFileFormatCheckProblem(Exception):
    def __init__(self, where):
        Exception.__init__(self, 'Illegal package format in {}. Please run `repology-update.py --parse` on all repositories to update the format.'.format(where))


class TooLittlePackages(Exception):
    def __init__(self, numpackages, minpackages):
        Exception.__init__(self, 'Unexpectedly small number of packages: {} when expected no less than {}'.format(numpackages, minpackages))


class InconsistentPackage(Exception):
    pass


class RepositoryProcessor:
    def __init__(self, repomgr, statedir, parseddir, safety_checks=True):
        self.repomgr = repomgr
        self.statedir = statedir
        self.parseddir = parseddir
        self.safety_checks = safety_checks

        self.fetcher_factory = ClassFactory('repology.fetchers.fetchers', superclass=Fetcher)
        self.parser_factory = ClassFactory('repology.parsers.parsers', superclass=Parser)

    def _get_state_path(self, repository):
        return os.path.join(self.statedir, repository['name'] + '.state')

    def _get_state_source_path(self, repository, source):
        return os.path.join(self._get_state_path(repository), source['name'].replace('/', '_'))

    def _get_parsed_path(self, repository):
        return os.path.join(self.parseddir, repository['name'] + '.parsed')

    def _get_parsed_chunk_paths(self, repository):
        dirpath = self._get_parsed_path(repository)
        return [
            os.path.join(dirpath, filename)
            for filename in os.listdir(dirpath)
        ] if os.path.isdir(dirpath) else []

    # source level private methods
    def _fetch_source(self, repository, update, source, logger):
        if 'fetcher' not in source:
            logger.log('fetching source {} not supported'.format(source['name']))
            return

        logger.log('fetching source {} started'.format(source['name']))

        self.fetcher_factory.SpawnWithKnownArgs(
            source['fetcher'], source
        ).fetch(
            self._get_state_source_path(repository, source),
            update=update,
            logger=logger.GetIndented()
        )

        logger.log('fetching source {} complete'.format(source['name']))

    def _iter_parse_source(self, repository, source, transformer, logger):
        def postprocess_parsed_packages(packages_iter):
            for package in packages_iter:
                # unwrap packagemaker
                if not package.check_sanity(verbose=True):
                    continue

                package = package.unwrap()

                # fill repository-specific fields
                package.repo = repository['name']
                package.family = repository['family']

                if 'subrepo' in source:
                    package.subrepo = source['subrepo']

                if repository.get('shadow', False):
                    package.shadow = True

                if not package.maintainers:
                    if 'default_maintainer' in repository:
                        package.maintainers = [repository['default_maintainer']]
                    else:
                        package.maintainers = ['fallback-mnt-{}@repology'.format(repository['name'])]

                # transform
                if transformer:
                    transformer.process(package)

                # skip removed packages
                if package.HasFlag(PackageFlags.remove):
                    continue

                # postprocess
                def strip_flavor(flavor):
                    if flavor.startswith(package.effname + '-'):
                        return flavor[len(package.effname) + 1:]
                    return flavor

                package.flavors = sorted(set(map(strip_flavor, package.flavors)))

                yield package

        return postprocess_parsed_packages(
            self.parser_factory.SpawnWithKnownArgs(
                source['parser'], source
            ).iter_parse(
                self._get_state_source_path(repository, source),
                PackageFactory(logger),
                transformer
            )
        )

    def _iter_parse_all_sources(self, repository, transformer, logger):
        for source in repository['sources']:
            logger.log('parsing source {} started'.format(source['name']))
            yield from self._iter_parse_source(repository, source, transformer, logger.GetIndented())
            logger.log('parsing source {} complete'.format(source['name']))

    # repository level private methods
    def _fetch(self, repository, update, logger):
        logger.log('fetching started')

        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        for source in repository['sources']:
            if not os.path.isdir(self._get_state_path(repository)):
                os.mkdir(self._get_state_path(repository))
            self._fetch_source(repository, update, source, logger.GetIndented())

        logger.log('fetching complete')

    def _parse(self, repository, transformer, logger):
        logger.log('parsing started')

        if not os.path.isdir(self.parseddir):
            os.mkdir(self.parseddir)

        packages = []
        chunknum = 0
        num_packages = 0

        def flush_packages():
            nonlocal packages, chunknum

            if packages:
                packages = sorted(packages, key=lambda package: package.effname)
                serialize(packages, os.path.join(state_dir, str(chunknum)))
                packages = []
                chunknum += 1

        with AtomicDir(self._get_parsed_path(repository)) as state_dir:
            for package in self._iter_parse_all_sources(repository, transformer, logger):
                packages.append(package)
                num_packages += 1

                if len(packages) >= MAX_PACKAGES_PER_CHUNK:
                    flush_packages()

            flush_packages()

            if self.safety_checks and num_packages < repository['minpackages']:
                raise TooLittlePackages(num_packages, repository['minpackages'])

        logger.log('parsing complete, {} packages'.format(num_packages))

    # public methods
    def fetch(self, reponames, update=True, logger=NoopLogger()):
        for repository in self.repomgr.GetRepositories(reponames):
            self._fetch(repository, update, logger)

    def parse(self, reponames, transformer=None, logger=NoopLogger()):
        for repository in self.repomgr.GetRepositories(reponames):
            self._parse(repository, transformer, logger)

    def iter_parse(self, reponames, transformer=None, logger=NoopLogger()):
        for repository in self.repomgr.GetRepositories(reponames):
            yield from self._iter_parse_all_sources(repository, transformer, logger)

    def iter_parsed(self, reponames=None, logger=NoopLogger()):
        def get_sources():
            for repository in self.repomgr.GetRepositories(reponames):
                sources = self._get_parsed_chunk_paths(repository)
                if not sources:
                    logger.log('parsed packages for repository {} are missing, treating repository as empty'.format(repository['desc']), severity=Logger.ERROR)
                yield from sources

        with heap_deserializer(get_sources(), lambda package: package.effname) as heap:
            for packageset in heap():
                packageset = PackagesetDeduplicate(packageset)

                yield packageset
