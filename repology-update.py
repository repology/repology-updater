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
from repology.transformer import PackageTransformer
from repology.logger import *


def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', default='_state', help='path to directory with repository state')
    parser.add_argument('-l', '--logfile', help='path to log file')
    parser.add_argument('-U', '--rules', default='rules.yaml', help='path to name transformation rules yaml')

    parser.add_argument('-f', '--fetch', action='count', help='allow fetching repository data (twice to also update)')
    parser.add_argument('-p', '--parse', action='store_true', help='parse, process and serialize repository data')

    # XXX: this is dangerous as long as ignored packages are removed from dumps
    parser.add_argument('-P', '--reprocess', action='store_true', help='reprocess repository data')

    parser.add_argument('-r', '--repository', action='append', help='specify repository names or tags to process')
    options = parser.parse_args()

    if not options.repository:
        options.repository = ["all"]

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repoman = RepositoryManager(options.statedir)
    transformer = PackageTransformer(options.rules)

    total_count = 0
    success_count = 0
    for reponame in repoman.GetNames(reponames=options.repository):
        repo_logger = logger.GetPrefixed(reponame + ": ")
        repo_logger.Log("started")
        try:
            if options.fetch:
                repoman.Fetch(reponame, update=(options.fetch >= 2), logger=repo_logger.GetIndented())
            if options.parse:
                repoman.ParseAndSerialize(reponame, transformer=transformer, logger=repo_logger.GetIndented())
            elif options.reprocess:
                repoman.Reprocess(reponame, transformer=transformer, logger=repo_logger.GetIndented())
        except KeyboardInterrupt:
            logger.Log("interrupted")
            return 1
        except:
            repo_logger.Log("failed, exception follows")
            for item in traceback.format_exception(*sys.exc_info()):
                for line in item.split('\n'):
                    if line:
                        repo_logger.GetIndented().Log(line)
        else:
            repo_logger.Log("complete")
            success_count += 1

        total_count += 1

    logger.Log("{}/{} repositories processed successfully".format(success_count, total_count))

    if options.parse or options.reprocess:
        unmatched = transformer.GetUnmatchedRules()
        if len(unmatched):
            wlogger = logger.GetPrefixed("WARNING: ")
            wlogger.Log("unmatched rules detected!")

            for rule in unmatched:
                wlogger.Log(rule)

    return 0 if success_count == total_count else 1

if __name__ == '__main__':
    os.sys.exit(Main())
