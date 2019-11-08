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

# mypy: no-disallow-untyped-calls

import argparse
import sys
from typing import Any, Iterable

from repology.config import config
from repology.logger import FileLogger, Logger, StderrLogger
from repology.package import Package, PackageFlags, PackageStatus
from repology.packageproc import fill_packageset_versions
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor


def format_package_field(key: str, value: Any) -> str:
    if key == 'versionclass':
        return PackageStatus.as_string(value)
    if key == 'flags':
        return PackageFlags.as_string(value)
    if isinstance(value, dict):
        return str({k: v for k, v in sorted(value.items())})
    return str(value).replace('\n', '\\n')


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=config['STATE_DIR'], help='path to directory with repository state')
    parser.add_argument('-P', '--parseddir', default=config['PARSED_DIR'], help='path to directory with parsed repository data')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=config['REPOS_DIR'], help='path directory with reposotory configs')

    parser.add_argument('-f', '--fields', default='repo,effname,version', help='fields to list for the package')
    parser.add_argument('-s', '--field-separator', default=' ', help='field separator')

    parser.add_argument('-a', '--all', action='store_true', help='dump all projects including shadow-only')

    parser.add_argument('--from', type=str, default=None, help='dump projects starting from the given name', dest='from_')
    parser.add_argument('--to', type=str, default=None, help='dump projects up to given name')

    parser.add_argument('reponames', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name to process')

    return parser.parse_args()


def packageset_is_shadow_only(packages: Iterable[Package]) -> bool:
    for package in packages:
        if not package.shadow:
            return False

    return True


def main() -> int:
    options = parse_arguments()

    logger: Logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    if options.fields == 'all':
        options.fields = ['effname', 'repo', 'version'] + [slot for slot in Package.__slots__ if slot not in ['effname', 'repo', 'version']]
    else:
        options.fields = options.fields.split(',')

    repomgr = RepositoryManager(options.repos_dir)
    repoproc = RepositoryProcessor(repomgr, options.statedir, options.parseddir)

    logger.log('dumping...')
    for packageset in repoproc.iter_parsed(reponames=options.reponames, logger=logger):
        if options.from_ is not None and packageset[0].effname < options.from_:
            continue
        if options.to is not None and packageset[0].effname > options.to:
            break

        fill_packageset_versions(packageset)

        if not options.all and packageset_is_shadow_only(packageset):
            continue

        for package in packageset:
            print(
                options.field_separator.join(
                    (
                        format_package_field(field, getattr(package, field)) for field in options.fields
                    )
                )
            )

    return 0


if __name__ == '__main__':
    sys.exit(main())
