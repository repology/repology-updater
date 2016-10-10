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
import traceback
from argparse import ArgumentParser

from repology.repoman import RepositoryManager
from repology.logger import *


def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', help='path to directory with repository state')
    parser.add_argument('-l', '--logfile', help='path to log file')

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

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repoman = RepositoryManager(options.statedir)

    total_count = 0
    success_count = 0
    for reponame in repoman.GetNames(tags=options.tag, repositories=options.repository):
        repo_logger = logger.GetPrefixed(reponame + ": ")
        repo_logger.Log("processing started")
        try:
            if options.fetch:
                repoman.FetchOne(reponame, update=options.update, logger=repo_logger.GetIndented())
            if options.parse:
                repoman.ParseAndSerializeOne(reponame, logger=repo_logger.GetIndented())
        except KeyboardInterrupt:
            logger.Log("processing interrupted")
            return 1
        except:
            repo_logger.Log("processing failed, exception follows")
            for item in traceback.format_exception(*sys.exc_info()):
                for line in item.split('\n'):
                    if line:
                        repo_logger.GetIndented().Log(line)
        else:
            repo_logger.Log("processing complete")
            success_count += 1

        total_count += 1

    logger.Log("{}/{} repositories processed successfully".format(success_count, total_count))

    return 0 if success_count == total_count else 1

if __name__ == '__main__':
    os.sys.exit(Main())
