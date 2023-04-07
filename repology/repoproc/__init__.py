# Copyright (C) 2016-2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from collections import defaultdict
from itertools import chain
from typing import Iterable, Iterator

from repology.atomic_fs import AtomicDir
from repology.fetchers import Fetcher
from repology.linkformatter import format_package_links
from repology.logger import Logger, NoopLogger
from repology.maintainermgr import MaintainerManager
from repology.moduleutils import ClassFactory
from repology.package import Package, PackageFlags, PackageLinkTuple
from repology.packagemaker import PackageFactory, PackageMaker
from repology.packageproc import packageset_deduplicate
from repology.parsers import Parser
from repology.repomgr import Repository, RepositoryManager, RepositoryNameList, Source
from repology.repoproc.serialization import ChunkedSerializer, heap_deserialize
from repology.transformer import PackageTransformer
from repology.utils.itertools import unicalize


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

    def _get_state_path(self, repository: Repository) -> str:
        return os.path.join(self.statedir, repository.name + '.state')

    def _get_state_source_path(self, repository: Repository, source: Source) -> str:
        return os.path.join(self._get_state_path(repository), source.name.replace('/', '_'))

    def _get_parsed_path(self, repository: Repository) -> str:
        return os.path.join(self.parseddir, repository.name + '.parsed')

    def _get_parsed_chunk_paths(self, repository: Repository) -> list[str]:
        dirpath = self._get_parsed_path(repository)
        return [
            os.path.join(dirpath, filename)
            for filename in os.listdir(dirpath)
        ] if os.path.isdir(dirpath) else []

    # source level private methods
    def _fetch_source(self, repository: Repository, update: bool, source: Source, logger: Logger) -> bool:
        logger.log(f'fetching source {source.name} started')

        fetcher: Fetcher = self.fetcher_factory.spawn(
            source.fetcher['class'],
            **{k: v for k, v in source.fetcher.items() if k != 'class'}
        )

        have_changes = fetcher.fetch(
            self._get_state_source_path(repository, source),
            update=update,
            logger=logger.get_indented()
        )

        logger.log(f'fetching source {source.name} complete' + ('' if have_changes else ' (no changes)'))

        return have_changes

    def _iter_parse_source(
        self,
        repository: Repository,
        source: Source,
        transformer: PackageTransformer | None,
        maintainermgr: MaintainerManager | None,
        logger: Logger
    ) -> Iterator[Package]:
        def postprocess_parsed_packages(packages_iter: Iterable[PackageMaker]) -> Iterator[Package]:
            for packagemaker in packages_iter:
                try:
                    package = packagemaker.spawn(
                        repo=repository.name,
                        family=repository.family,
                        subrepo=source.subrepo,
                        shadow=repository.shadow,
                        default_maintainer=repository.default_maintainer,
                    )
                except RuntimeError as e:
                    packagemaker.log(str(e), Logger.ERROR)
                    raise

                # add packagelinks
                packagelinks: dict[int, list[PackageLinkTuple]] = defaultdict(list)
                for pkglink in source.packagelinks + repository.packagelinks:
                    try:
                        packagelinks[pkglink.priority].extend(
                            (pkglink.type, *url.split('#', 1))  # type: ignore
                            for url in format_package_links(package, pkglink.url)
                        )
                    except Exception as e:
                        packagemaker.log(f'cannot spawn package link from template "{pkglink.url}": {str(e)}', Logger.ERROR)
                        raise

                if package.links:
                    packagelinks[0].extend(package.links)

                package.links = list(
                    unicalize(
                        chain.from_iterable(
                            links for _, links in sorted(
                                packagelinks.items(),
                                # stable descending sort on priority
                                key=lambda t: t[0],
                                reverse=True
                            )
                        )
                    )
                )

                # transform
                if transformer:
                    transformer.process(package)

                # skip removed packages
                if package.has_flag(PackageFlags.REMOVE):
                    continue

                # postprocess flavors
                def strip_flavor(flavor: str) -> str:
                    flavor.removeprefix(package.effname + '-')
                    return flavor

                package.flavors = sorted(set(map(strip_flavor, package.flavors)))

                # postprocess maintainers
                if maintainermgr and package.maintainers:
                    package.maintainers = [maintainer for maintainer in package.maintainers if not maintainermgr.is_hidden(maintainer)]

                yield package

        return postprocess_parsed_packages(
            self.parser_factory.spawn(
                source.parser['class'],
                **{k: v for k, v in source.parser.items() if k != 'class'}
            ).iter_parse(
                self._get_state_source_path(repository, source),
                PackageFactory(logger)
            )
        )

    def _iter_parse_all_sources(
        self,
        repository: Repository,
        transformer: PackageTransformer | None,
        maintainermgr: MaintainerManager | None,
        logger: Logger
    ) -> Iterator[Package]:
        for source in repository.sources:
            logger.log(f'parsing source {source.name} started')
            yield from self._iter_parse_source(repository, source, transformer, maintainermgr, logger.get_indented())
            logger.log(f'parsing source {source.name} complete')

    # repository level private methods
    def _fetch(self, repository: Repository, update: bool, logger: Logger) -> bool:
        logger.log('fetching started')

        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        have_changes = False
        for source in repository.sources:
            if not os.path.isdir(self._get_state_path(repository)):
                os.mkdir(self._get_state_path(repository))
            have_changes |= self._fetch_source(repository, update, source, logger.get_indented())

        logger.log('fetching complete' + ('' if have_changes else ' (no changes)'))

        return have_changes

    def _parse(
        self,
        repository: Repository,
        transformer: PackageTransformer | None,
        maintainermgr: MaintainerManager | None,
        logger: Logger
    ) -> None:
        logger.log('parsing started')

        if not os.path.isdir(self.parseddir):
            os.mkdir(self.parseddir)

        with AtomicDir(self._get_parsed_path(repository)) as state_dir:
            serializer = ChunkedSerializer(state_dir.get_path(), MAX_PACKAGES_PER_CHUNK)

            serializer.serialize(self._iter_parse_all_sources(repository, transformer, maintainermgr, logger))

            if self.safety_checks and serializer.get_num_packages() < repository.minpackages:
                raise TooLittlePackages(serializer.get_num_packages(), repository.minpackages)

        logger.log('parsing complete, {} packages'.format(serializer.get_num_packages()))

    # public methods
    def fetch(self, reponames: RepositoryNameList, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        have_changes = False

        for repository in self.repomgr.get_repositories(reponames):
            have_changes |= self._fetch(repository, update, logger)

        return have_changes

    def parse(
        self,
        reponames: RepositoryNameList,
        transformer: PackageTransformer | None = None,
        maintainermgr: MaintainerManager | None = None,
        logger: Logger = NoopLogger()
    ) -> None:
        for repository in self.repomgr.get_repositories(reponames):
            self._parse(repository, transformer, maintainermgr, logger)

    def iter_parse(
        self,
        reponames: RepositoryNameList,
        transformer: PackageTransformer | None = None,
        maintainermgr: MaintainerManager | None = None,
        logger: Logger = NoopLogger()
    ) -> Iterator[Package]:
        for repository in self.repomgr.get_repositories(reponames):
            yield from self._iter_parse_all_sources(repository, transformer, maintainermgr, logger)

    def iter_parsed(self, reponames: RepositoryNameList | None = None, logger: Logger = NoopLogger()) -> Iterator[list[Package]]:
        sources: list[str] = []
        for repository in self.repomgr.get_repositories(reponames):
            repo_sources = self._get_parsed_chunk_paths(repository)

            if not repo_sources:
                logger.log(f'parsed packages for repository {repository.desc} are missing, treating repository as empty', severity=Logger.WARNING)

            sources.extend(repo_sources)

        if sources:
            yield from map(packageset_deduplicate, heap_deserialize(sources))
        else:
            logger.log('no parsed packages found', severity=Logger.ERROR)
