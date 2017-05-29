#!/usr/bin/env python3
#
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

import argparse
import os

import repology.config
from repology.filters import *
from repology.logger import *
from repology.package import *
from repology.packageproc import *
from repology.repoman import RepositoryManager


def PackageVersionClass2Letter(value):
    if value == PackageVersionClass.newest:
        return 'N'
    elif value == PackageVersionClass.outdated:
        return 'O'
    elif value == PackageVersionClass.ignored:
        return 'I'
    else:
        return '?'


def RepositoryVersionClass2Letter(value):
    if value == RepositoryVersionClass.newest:
        return 'N'
    elif value == RepositoryVersionClass.outdated:
        return 'O'
    elif value == RepositoryVersionClass.mixed:
        return 'M'
    elif value == RepositoryVersionClass.ignored:
        return 'I'
    elif value == RepositoryVersionClass.lonely:
        return 'L'
    else:
        return '?'


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=repology.config.STATE_DIR, help='path to directory with repository state')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=repology.config.REPOS_DIR, help='path directory with reposotory configs')
    parser.add_argument('-M', '--mode', choices=['batch', 'stream'], default='stream', help='processing mode')

    filters_grp = parser.add_argument_group('Filters')
    filters_grp.add_argument('--no-shadow', action='store_true', help='treat shadow repositories as normal')
    filters_grp.add_argument('--maintainer', help='filter by maintainer')
    filters_grp.add_argument('--category', help='filter by category')
    filters_grp.add_argument('--less-repos', help='filter by number of repos')
    filters_grp.add_argument('--more-repos', help='filter by number of repos')
    filters_grp.add_argument('--in-repository', help='filter by presence in repository')
    filters_grp.add_argument('--not-in-repository', help='filter by absence in repository')
    filters_grp.add_argument('--outdated-in-repository', help='filter by outdatedness in repository')

    parser.add_argument('-D', '--dump', choices=['packages', 'summaries'], default='packages', help='dump mode')
    parser.add_argument('-f', '--fields', default='repo,effname,version', help='fields to list for the package')
    parser.add_argument('-s', '--field-separator', default=' ', help='field separator')

    parser.add_argument('reponames', default=repology.config.REPOSITORIES, metavar='repo|tag', nargs='*', help='repository or tag name to process')
    options = parser.parse_args()

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    if options.fields == 'all':
        options.fields = sorted(Package().__dict__.keys())
    else:
        options.fields = options.fields.split(',')

    # Set up filters
    filters = []
    if options.maintainer:
        filters.append(MaintainerFilter(options.maintainer))
    if options.category:
        filters.append(CategoryFilter(options.maintainer))
    if options.more_repos is not None or options.less_repos is not None:
        filters.append(FamilyCountFilter(more=options.more_repos, less=options.less_repos))
    if options.in_repository:
        filters.append(InRepoFilter(options.in_repository))
    if options.not_in_repository:
        filters.append(NotInRepoFilter(options.not_in_repository))
    if options.outdated_in_repository:
        filters.append(OutdatedInRepoFilter(options.not_in_repository))
    if not options.no_shadow:
        filters.append(ShadowFilter())

    repoman = RepositoryManager(options.repos_dir, options.statedir)

    def PackageProcessor(packageset):
        FillPackagesetVersions(packageset)

        if not PackagesetCheckFilters(packageset, *filters):
            return

        if options.dump == 'packages':
            for package in packageset:
                print(
                    options.field_separator.join(
                        [
                            str(getattr(package, field)) for field in options.fields
                        ]
                    )
                )
        if options.dump == 'summaries':
            print(packageset[0].effname)
            summaries = PackagesetToSummaries(packageset)
            for reponame in repoman.GetNames(options.reponames):
                if reponame in summaries:
                    print('  {}: {} ({}) *{}'.format(
                        reponame,
                        summaries[reponame]['version'],
                        RepositoryVersionClass2Letter(summaries[reponame]['versionclass']),
                        summaries[reponame]['numpackages'],
                    ))

    if options.mode == 'stream':
        logger.Log('dumping...')
        repoman.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)
    else:
        logger.Log('loading packages...')
        all_packages = repoman.DeserializeMulti(reponames=options.reponames, logger=logger)
        logger.Log('merging packages...')
        metapackages = PackagesToMetapackages(all_packages)
        logger.Log('dumping...')
        for metapackage_name, packageset in sorted(metapackages.items()):
            PackageProcessor(packageset)

    return 0


if __name__ == '__main__':
    os.sys.exit(Main())
