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
from typing import Iterable, Iterator, List, Optional

from repology.atomic_fs import AtomicDir
from repology.fetchers import Fetcher
from repology.logger import Logger, NoopLogger
from repology.moduleutils import ClassFactory
from repology.package import Package, PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.packageproc import packageset_deduplicate
from repology.parsers import Parser
from repology.repomgr import RepositoryManager, RepositoryMetadata, RepositoryNameList
from repology.repoproc.serialization import ChunkedSerializer, heap_deserialize
from repology.transformer import PackageTransformer


MAX_PACKAGES_PER_CHUNK = 10240


class StateFileFormatCheckProblem(Exception):
    def __init__(self, where: str) -> None:
        Exception.__init__(self, 'Illegal package format in {}. Please run `repology-update.py --parse` on all repositories to update the format.'.format(where))


class TooLittlePackages(Exception):
    def __init__(self, numpackages: int, minpackages: int) -> None:
        Exception.__init__(self, 'Unexpectedly small number of packages: {} when expected no less than {}'.format(numpackages, minpackages))


class InconsistentPackage(Exception):
    pass


class RepositoryProcessor:
    def __init__(self, repomgr: RepositoryManager, statedir: str, parseddir: str, safety_checks: bool = True) -> None:
        self.repomgr = repomgr
        self.statedir = statedir
        self.parseddir = parseddir
        self.safety_checks = safety_checks

        self.fetcher_factory = ClassFactory('repology.fetchers.fetchers', superclass=Fetcher)
        self.parser_factory = ClassFactory('repology.parsers.parsers', superclass=Parser)

    def _get_state_path(self, repository: RepositoryMetadata) -> str:
        return os.path.join(self.statedir, repository['name'] + '.state')

    def _get_state_source_path(self, repository: RepositoryMetadata, source: RepositoryMetadata) -> str:
        return os.path.join(self._get_state_path(repository), source['name'].replace('/', '_'))

    def _get_parsed_path(self, repository: RepositoryMetadata) -> str:
        return os.path.join(self.parseddir, repository['name'] + '.parsed')

    def _get_parsed_chunk_paths(self, repository: RepositoryMetadata) -> List[str]:
        dirpath = self._get_parsed_path(repository)
        return [
            os.path.join(dirpath, filename)
            for filename in os.listdir(dirpath)
        ] if os.path.isdir(dirpath) else []

    # source level private methods
    def _fetch_source(self, repository: RepositoryMetadata, update: bool, source: RepositoryMetadata, logger: Logger) -> bool:
        if 'fetcher' not in source:
            logger.log('fetching source {} not supported'.format(source['name']))
            return False

        logger.log('fetching source {} started'.format(source['name']))

        fetcher: Fetcher = self.fetcher_factory.spawn_with_known_args(
            source['fetcher'],
            source
        )

        have_changes = fetcher.fetch(
            self._get_state_source_path(repository, source),
            update=update,
            logger=logger.get_indented()
        )

        logger.log('fetching source {} complete'.format(source['name']) + ('' if have_changes else ' (no changes)'))

        return have_changes

    def _iter_parse_source(self, repository: RepositoryMetadata, source: RepositoryMetadata, transformer: Optional[PackageTransformer], logger: Logger) -> Iterator[Package]:
        def postprocess_parsed_packages(packages_iter: Iterable[PackageMaker]) -> Iterator[Package]:
            for packagemaker in packages_iter:
                # unwrap packagemaker
                if not packagemaker.check_sanity(verbose=True):
                    continue

                package = packagemaker.unwrap()

                # fill repository-specific fields
                package.repo = repository['name']
                package.family = repository['family']

                if 'subrepo' in source:
                    package.subrepo = source['subrepo']

                if repository.get('shadow', False):
                    package.shadow = True

                if not package.maintainers and 'default_maintainer' in repository:
                    package.maintainers = [repository['default_maintainer']]

                # transform
                if transformer:
                    transformer.process(package)

                # skip removed packages
                if package.has_flag(PackageFlags.REMOVE):
                    continue

                # postprocess
                def strip_flavor(flavor: str) -> str:
                    if flavor.startswith(package.effname + '-'):
                        return flavor[len(package.effname) + 1:]
                    return flavor

                package.flavors = sorted(set(map(strip_flavor, package.flavors)))

                yield package

        return postprocess_parsed_packages(
            self.parser_factory.spawn_with_known_args(
                source['parser'], source
            ).iter_parse(
                self._get_state_source_path(repository, source),
                PackageFactory(logger),
                transformer
            )
        )

    def _iter_parse_all_sources(self, repository: RepositoryMetadata, transformer: Optional[PackageTransformer], logger: Logger) -> Iterator[Package]:
        for source in repository['sources']:
            logger.log('parsing source {} started'.format(source['name']))
            yield from self._iter_parse_source(repository, source, transformer, logger.get_indented())
            logger.log('parsing source {} complete'.format(source['name']))

    # repository level private methods
    def _fetch(self, repository: RepositoryMetadata, update: bool, logger: Logger) -> bool:
        logger.log('fetching started')

        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        have_changes = False
        for source in repository['sources']:
            if not os.path.isdir(self._get_state_path(repository)):
                os.mkdir(self._get_state_path(repository))
            have_changes |= self._fetch_source(repository, update, source, logger.get_indented())

        logger.log('fetching complete' + ('' if have_changes else ' (no changes)'))

        return have_changes

    def _parse(self, repository: RepositoryMetadata, transformer: Optional[PackageTransformer], logger: Logger) -> None:
        logger.log('parsing started')

        if not os.path.isdir(self.parseddir):
            os.mkdir(self.parseddir)

        with AtomicDir(self._get_parsed_path(repository)) as state_dir:
            serializer = ChunkedSerializer(state_dir.get_path(), MAX_PACKAGES_PER_CHUNK)

            serializer.serialize(self._iter_parse_all_sources(repository, transformer, logger))

            if self.safety_checks and serializer.get_num_packages() < repository['minpackages']:
                raise TooLittlePackages(serializer.get_num_packages(), repository['minpackages'])

        logger.log('parsing complete, {} packages'.format(serializer.get_num_packages()))

    # public methods
    def fetch(self, reponames: RepositoryNameList, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        have_changes = False

        for repository in self.repomgr.get_repositories(reponames):
            have_changes |= self._fetch(repository, update, logger)

        return have_changes

    def parse(self, reponames: RepositoryNameList, transformer: Optional[PackageTransformer] = None, logger: Logger = NoopLogger()) -> None:
        for repository in self.repomgr.get_repositories(reponames):
            self._parse(repository, transformer, logger)

    def iter_parse(self, reponames: RepositoryNameList, transformer: Optional[PackageTransformer] = None, logger: Logger = NoopLogger()) -> Iterator[Package]:
        for repository in self.repomgr.get_repositories(reponames):
            yield from self._iter_parse_all_sources(repository, transformer, logger)

    def iter_parsed(self, reponames: Optional[RepositoryNameList] = None, logger: Logger = NoopLogger()) -> Iterator[List[Package]]:
        sources: List[str] = []
        for repository in self.repomgr.get_repositories(reponames):
            repo_sources = self._get_parsed_chunk_paths(repository)

            if not repo_sources:
                logger.log('parsed packages for repository {} are missing, treating repository as empty'.format(repository['desc']), severity=Logger.WARNING)

            sources.extend(repo_sources)

        if sources:
            yield from map(packageset_deduplicate, heap_deserialize(sources))
        else:
            logger.log('no parsed packages found', severity=Logger.ERROR)
