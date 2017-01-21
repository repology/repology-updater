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
import argparse
import requests

from repology.database import Database
from repology.logger import StderrLogger, FileLogger

import repology.config


def GetLinkStatus(link):
    try:
        response = requests.head(link, allow_redirects=True, headers={'user-agent': "Repology link checker/0"})

        redirect = None
        size = None
        location = None

        # handle redirect chain
        if response.history:
            redirect = response.history[0].status_code

            # resolve permanent (and only permament!) redirect chain
            for h in response.history:
                if h.status_code == 301:
                    location = h.headers.get('location')

        # handle size
        if response.status_code == 200:
            content_length = response.headers.get('content-length')
            if content_length:
                size = int(content_length)

        return (response.status_code, redirect, size, location)
    except KeyboardInterrupt:
        raise
    except requests.Timeout:
        return (Database.linkcheck_status_timeout, None, None, None)
    except requests.TooManyRedirects:
        return (Database.linkcheck_status_too_many_redirects, None, None, None)
    except requests.ConnectionError:
        return (Database.linkcheck_status_cannot_connect, None, None, None)
    except:
        raise
        return (Database.linkcheck_status_unknown_error, None, None, None)


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-D', '--dsn', default=repology.config.DSN, help='database connection params')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')

    parser.add_argument('-t', '--timeout', type=int, default=60, help='timeout for link requests in seconds')
    parser.add_argument('-a', '--age', type=int, default=365, help='min age for recheck in days')
    parser.add_argument('-p', '--packsize', type=int, default=128, help='pack size for link processing')
    options = parser.parse_args()

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    database = Database(options.dsn, readonly=False)

    logger.Log("Updating links table")
    database.ExtractLinks()
    logger.Log("Done, committing")
    database.Commit()
    logger.Log("  Committed")

    while True:
        logger.Log("Requesting pack of links")
        links = database.GetLinksForCheck(options.packsize, options.age * 60 * 60 * 24)
        if not links:
            logger.Log("  Empty pack, we're done")
            break
        else:
            logger.Log("  {} links(s)".format(len(links)))

        results = []
        for link in links:
            # XXX: add support for gentoo mirrors, skip for now
            if not link.startswith("http://") and not link.startswith("https://"):
                logger.Log("  Skipping {}, unsupported schema".format(link))
                continue

            logger.Log("  Processing {}".format(link))

            status, redirect, size, location = GetLinkStatus(link)

            if status == Database.linkcheck_status_timeout:
                logger.Log("    Failed, timeout")
            elif status == Database.linkcheck_status_too_many_redirects:
                logger.Log("    Failed, too many redirects")
            elif status == Database.linkcheck_status_unknown_error:
                logger.Log("    Failed, unknown exception")
            elif status == Database.linkcheck_status_cannot_connect:
                logger.Log("    Failed, connection error")
            else:
                logger.Log("    Status: {}, redirect: {}, size: {}, final location: {}".format(status, redirect, size, location))

            results.append((link, status, redirect, size, location))

        logger.Log("Writing pack")

        for result in results:
            link, status, redirect, size, location = result
            database.UpdateLinkStatus(link, status=status, redirect=redirect, size=size, location=location)

        logger.Log("Committing pack")
        database.Commit()
        logger.Log("  Committed")

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
