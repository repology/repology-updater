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
import html
import os
import sys
from random import shuffle

import repology.config
from repology.database import Database


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-D', '--dsn', default=repology.config.DSN, help='database connection params')

    parser.add_argument('-w', '--www-home', default=repology.config.REPOLOGY_HOME, help='repology www home')
    parser.add_argument('-m', '--max-urls', default=50000, help='max number of urls to generate')

    parser.add_argument('--main', action='store_true', help='generate maintainers sitemap')
    parser.add_argument('--metapackages', action='store_true', help='generate maintainers sitemap')

    options = parser.parse_args()

    database = Database(options.dsn, readonly=True)

    urls = []
    if options.main:
        urls = ['/', '/news', '/statistics', '/about', '/api/v1', '/repositories/']

        urls.extend(map(lambda row: '/maintainer/' + row[0], database.Query('SELECT maintainer FROM maintainers')))
        urls.extend(map(lambda row: '/repository/' + row[0], database.Query('SELECT name FROM repositories')))
    elif options.metapackages:
        LINKS_PER_METAPACKAGE = 3

        print('Guessing threshold for important metapackages', file=sys.stderr)

        num_repos = 1
        while True:
            num_metapackages = database.Query(
                'SELECT count(DISTINCT effname) FROM metapackage_repocounts WHERE num_families >= %s',
                num_repos
            )[0][0]

            num_urls_total = len(urls) + num_metapackages * LINKS_PER_METAPACKAGE

            print('Threshold = {}, {} metapackages, {} total urls'.format(num_repos, num_metapackages, num_urls_total), file=sys.stderr)

            if num_urls_total <= options.max_urls:
                print('  Looks good', file=sys.stderr)
                break

            if num_repos > 20:
                print('  Giving up, will truncate metapackage list', file=sys.stderr)
                break

            num_repos += 1

        # get most important packages
        for row in database.Query(
                'SELECT DISTINCT effname FROM metapackage_repocounts WHERE num_families >= %s LIMIT %s',
                num_repos,
                (options.max_urls - len(urls)) // LINKS_PER_METAPACKAGE):
            urls.append('/metapackage/' + row[0] + '/versions')
            urls.append('/metapackage/' + row[0] + '/packages')
            urls.append('/metapackage/' + row[0] + '/information')

        # fill the remaining space with less important packages
        for row in database.Query(
                'SELECT DISTINCT effname FROM metapackage_repocounts WHERE num_families = %s LIMIT %s',
                num_repos - 1,
                (options.max_urls - len(urls)) // LINKS_PER_METAPACKAGE):
            urls.append('/metapackage/' + row[0] + '/versions')
            urls.append('/metapackage/' + row[0] + '/packages')
            urls.append('/metapackage/' + row[0] + '/information')
    else:
        print('Please specify output mode', file=sys.stderr)

    shuffle(urls)

    # write XML
    print('Writing XML', file=sys.stderr)

    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        print('<url><loc>' + html.escape(options.www_home + url) + '</loc><changefreq>daily</changefreq></url>')
    print('</urlset>')

    return 0


if __name__ == '__main__':
    os.sys.exit(Main())
