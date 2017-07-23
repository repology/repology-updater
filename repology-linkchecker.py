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
import multiprocessing
import os
import re
import socket
import time
import urllib.parse

import requests

import repology.config
from repology.database import Database
from repology.logger import FileLogger, StderrLogger


def GetHTTPLinkStatus(url, timeout):
    try:
        response = requests.head(url, allow_redirects=True, headers={'user-agent': 'Repology link checker/0'}, timeout=timeout)

        # fallback to GET
        if response.status_code != 200:
            response = requests.get(url, allow_redirects=True, headers={'user-agent': 'Repology link checker/0'}, timeout=timeout)

        redirect = None
        size = None
        location = None

        # handle redirect chain
        if response.history:
            redirect = response.history[0].status_code

            # resolve permanent (and only permament!) redirect chain
            for h in response.history:
                if h.status_code == 301:
                    location = urllib.parse.urljoin(h.url, h.headers.get('location'))

        # handle size
        if response.status_code == 200:
            content_length = response.headers.get('content-length')
            if content_length:
                size = int(content_length)

        return (url, response.status_code, redirect, size, location)
    except KeyboardInterrupt:
        raise
    except requests.Timeout:
        return (url, Database.linkcheck_status_timeout, None, None, None)
    except requests.TooManyRedirects:
        return (url, Database.linkcheck_status_too_many_redirects, None, None, None)
    except requests.ConnectionError:
        # check for DNS error additionally
        try:
            parsed = urllib.parse.urlparse(url)
            socket.gethostbyname(parsed.hostname)
        except socket.gaierror:
            return (url, Database.linkcheck_status_dns_error, None, None, None)
        except:
            pass
        return (url, Database.linkcheck_status_cannot_connect, None, None, None)
    except requests.exceptions.InvalidURL:
        return (url, Database.linkcheck_status_invalid_url, None, None, None)
    except:
        return (url, Database.linkcheck_status_unknown_error, None, None, None)


def GetLinkStatuses(urls, delay, timeout):
    results = []
    prev_host = None
    for url in urls:
        # XXX: add support for gentoo mirrors, skip for now
        if not url.startswith('http://') and not url.startswith('https://'):
            continue

        host = urllib.parse.urlparse(url).hostname

        if host and host == prev_host:
            time.sleep(delay)

        results.append(GetHTTPLinkStatus(url, timeout))

        prev_host = host

    return results


def LinkProcessorWorker(queue, workerid, options, logger):
    database = Database(options.dsn, readonly=False)

    logger = logger.GetPrefixed('worker{}: '.format(workerid))

    logger.Log('Worker spawned')

    while True:
        pack = queue.get()
        if pack is None:
            logger.Log('Worker exiting')
            return

        logger.Log('Processing {} urls ({}..{})'.format(len(pack), pack[0], pack[-1]))
        for result in GetLinkStatuses(pack, delay=options.delay, timeout=options.timeout):
            url, status, redirect, size, location = result
            database.UpdateLinkStatus(url=url, status=status, redirect=redirect, size=size, location=location)

        database.Commit()
        logger.Log('Done processing {} urls ({}..{})'.format(len(pack), pack[0], pack[-1]))


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dsn', default=repology.config.DSN, help='database connection params')
    parser.add_argument('--logfile', help='path to log file (log to stderr by default)')

    parser.add_argument('--timeout', type=float, default=60.0, help='timeout for link requests in seconds')
    parser.add_argument('--delay', type=float, default=3.0, help='delay between requests to one host')
    parser.add_argument('--age', type=int, default=0, help='min age for recheck in days')
    parser.add_argument('--packsize', type=int, default=128, help='pack size for link processing')
    parser.add_argument('--maxpacksize', type=int, help='max pack size for link processing (useful to skip large hosts)')
    parser.add_argument('--jobs', type=int, default=1, help='number of parallel jobs')

    parser.add_argument('--unchecked', action='store_true', help='only process unchecked (newly discovered) links')
    parser.add_argument('--checked', action='store_true', help='only process old (already checked) links')
    parser.add_argument('--failed', action='store_true', help='only process links that were checked and failed')
    parser.add_argument('--succeeded', action='store_true', help='only process links that were checked and failed')
    parser.add_argument('--prefix', help='only process links with specified prefix')
    options = parser.parse_args()

    logger = FileLogger(options.logfile) if options.logfile else StderrLogger()
    database = Database(options.dsn, readonly=True, autocommit=True)

    queue = multiprocessing.Queue(1)
    processpool = [multiprocessing.Process(target=LinkProcessorWorker, args=(queue, i, options, logger)) for i in range(options.jobs)]
    for process in processpool:
        process.start()

    # base logger already passed to workers, may append prefix here
    logger = logger.GetPrefixed('master: ')

    prev_url = None
    while True:
        # Get pack of links
        logger.Log('Requesting pack of urls')
        urls = database.GetLinksForCheck(
            after=prev_url,
            prefix=options.prefix,  # no limit by default
            limit=options.packsize,
            recheck_age=options.age * 60 * 60 * 24,
            unchecked_only=options.unchecked,
            checked_only=options.checked,
            failed_only=options.failed,
            succeeded_only=options.succeeded
        )
        if not urls:
            logger.Log('  No more urls to process')
            break

        # Get another pack of urls with the last hostname to ensure
        # that all urls for one hostname get into a same large pack
        match = re.match('([a-z]+://[^/]+/)', urls[-1])
        if match:
            urls += database.GetLinksForCheck(
                after=urls[-1],
                prefix=match.group(1),
                recheck_age=options.age * 60 * 60 * 24,
                unchecked_only=options.unchecked,
                checked_only=options.checked,
                failed_only=options.failed,
                succeeded_only=options.succeeded
            )

        # Process
        if options.maxpacksize and len(urls) > options.maxpacksize:
            logger.Log('Skipping {} urls ({}..{}), exceeds max pack size'.format(len(urls), urls[0], urls[-1]))
        else:
            queue.put(urls)
            logger.Log('Enqueued {} urls ({}..{})'.format(len(urls), urls[0], urls[-1]))

        prev_url = urls[-1]

    logger.Log('Waiting for child processes to exit')

    for process in processpool:
        queue.put(None)

    for process in processpool:
        process.join()

    logger.Log('Done')

    return 0


if __name__ == '__main__':
    os.sys.exit(Main())
