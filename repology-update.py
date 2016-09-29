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
    parser.add_argument('-s', '--statedir', help='directory to store repository state')
    parser.add_argument('-U', '--no-update', action='store_true', help='only fetch for the first time, don\'t update')
    parser.add_argument('-t', '--tag', help='only process repositories with this tag', action='append')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose status')
    parser.add_argument('repository', help='repository to process', nargs='*')
    options = parser.parse_args()

    if options.statedir is None:
        raise RuntimeError("please set --statedir")

    repoman = RepositoryManager(options.statedir)

    print("===> Downloading package data...", file=sys.stderr)
    repoman.Fetch(
        update = not options.no_update,
        verbose = options.verbose,
        tags = options.tag,
        names = options.repository if options.repository else None
    )

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
