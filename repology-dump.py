#!/usr/bin/env python3
#
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

import argparse
import os

from repology.config import config
from repology.logger import FileLogger, StderrLogger
from repology.package import Package, VersionClass
from repology.packageproc import FillPackagesetVersions, PackagesetToBestByRepo
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor


def format_package_field(key, value):
    if key == 'versionclass':
        return VersionClass.ToString(value)
    if isinstance(value, dict):
        return str({k: v for k, v in sorted(value.items())})
    return str(value)


def parse_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=config['STATE_DIR'], help='path to directory with repository state')
    parser.add_argument('-P', '--parseddir', default=config['PARSED_DIR'], help='path to directory with parsed repository data')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=config['REPOS_DIR'], help='path directory with reposotory configs')

    parser.add_argument('-D', '--dump', choices=['packages', 'summaries'], default='packages', help='dump mode')
    parser.add_argument('-f', '--fields', default='repo,effname,version', help='fields to list for the package')
    parser.add_argument('-s', '--field-separator', default=' ', help='field separator')

    parser.add_argument('-a', '--all', action='store_true', help='dump all projects including shadow-only')

    parser.add_argument('reponames', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name to process')

    return parser.parse_args()


def packageset_is_shadow_only(packages):
    for package in packages:
        if not package.shadow:
            return False

    return True


def main():
    options = parse_arguments()

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    if options.fields == 'all':
        options.fields = sorted(Package().__dict__.keys())
    else:
        options.fields = options.fields.split(',')

    repomgr = RepositoryManager(options.repos_dir)
    repoproc = RepositoryProcessor(repomgr, options.statedir, options.parseddir)

    logger.Log('dumping...')
    for packageset in repoproc.iter_parsed(reponames=options.reponames):
        FillPackagesetVersions(packageset)

        if not options.all and packageset_is_shadow_only(packageset):
            continue

        if options.dump == 'packages':
            for package in packageset:
                print(
                    options.field_separator.join(
                        (
                            format_package_field(field, getattr(package, field)) for field in options.fields
                        )
                    )
                )
        if options.dump == 'summaries':
            print(packageset[0].effname)
            best_pkg_by_repo = PackagesetToBestByRepo(packageset)
            for reponame in repomgr.GetNames(options.reponames):
                if reponame in best_pkg_by_repo:
                    print('  {}: {} ({})'.format(
                        reponame,
                        best_pkg_by_repo[reponame].version,
                        VersionClass.ToString(best_pkg_by_repo[reponame].versionclass)
                    ))

    return 0


if __name__ == '__main__':
    os.sys.exit(main())
