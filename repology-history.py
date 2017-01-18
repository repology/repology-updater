#!/usr/bin/env python3
#
# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import argparse

from repology.database import Database

import repology.config


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-D', '--dsn', default=repology.config.DSN, help='database connection params')
    parser.add_argument('-u', '--update', action='store_true', help='update histories');

    options = parser.parse_args()

    database = Database(options.dsn, readonly=not options.update)

    if options.update:
        print("Saving repositories snapshot...", file=sys.stderr)
        database.SnapshotRepositoriesHistory()

        print("Committing...", file=sys.stderr)
        database.Commit()

        print("Done!", file=sys.stderr)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
