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
from argparse import ArgumentParser

from repology.repositories import RepositoryManager

def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', help='path to directory with repository state')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    parser.add_argument('-f', '--fetch', action='store_true', help='allow fetching repository data')
    parser.add_argument('-u', '--update', action='store_true', help='allow updating repository data')
    parser.add_argument('-p', '--parse', action='store_true', help='parse and serialize repository data')

    parser.add_argument('-t', '--tag', action='append', help='only process repositories with this tag')
    parser.add_argument('-r', '--repository', action='append', help='only process repositories with this name')
    options = parser.parse_args()

    if not options.statedir:
        raise RuntimeError("please set --statedir")
    if not options.tag and not options.repository:
        raise RuntimeError("please set --tag or --repository")

    repoman = RepositoryManager(options.statedir)

    if options.fetch:
        repoman.Fetch(
            update = options.update,
            verbose = options.verbose,
            tags = options.tag,
            repositories = options.repository
        )

    if options.parse:
        repoman.ParseAndSerialize(
            verbose = options.verbose,
            tags = options.tag,
            repositories = options.repository
        )

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
