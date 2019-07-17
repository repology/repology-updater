#!/usr/bin/env python3
#
# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import pickle
import sys
import time
from typing import Any, Dict, List, Optional

from repology.config import config
from repology.database import Database
from repology.querymgr import QueryManager


queries = [
    ('query_metapackages', 'metapackages all >=a', {'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages all <=z', {'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages search >=a', {'search': 'ifo', 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages search <=z', {'search': 'ifo', 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo >=a', {'inrepo': 'freebsd', 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo <=z', {'inrepo': 'freebsd', 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages notrepo >=a', {'notinrepo': 'freebsd', 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages notrepo <=z', {'notinrepo': 'freebsd', 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo newest >=a', {'inrepo': 'freebsd', 'newest': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo newest <=z', {'inrepo': 'freebsd', 'newest': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo outdated >=a', {'inrepo': 'freebsd', 'outdated': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo outdated <=z', {'inrepo': 'freebsd', 'outdated': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo problematic >=a', {'inrepo': 'freebsd', 'problematic': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo problematic <=z', {'inrepo': 'freebsd', 'problematic': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo notrepo >=a', {'inrepo': 'freebsd', 'notinrepo': 'debian_unstable', 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo notrepo <=z', {'inrepo': 'freebsd', 'notinrepo': 'debian_unstable', 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer >=a', {'maintainer': 'amdmi3@freebsd.org', 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer <=z', {'maintainer': 'amdmi3@freebsd.org', 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer newest >=a', {'maintainer': 'amdmi3@freebsd.org', 'newest': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer newest <=z', {'maintainer': 'amdmi3@freebsd.org', 'newest': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer outdated >=a', {'maintainer': 'amdmi3@freebsd.org', 'outdated': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer outdated <=z', {'maintainer': 'amdmi3@freebsd.org', 'outdated': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer problematic >=a', {'maintainer': 'amdmi3@freebsd.org', 'problematic': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages maintainer problematic <=z', {'maintainer': 'amdmi3@freebsd.org', 'problematic': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages families ==1 >=a', {'max_families': 1, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages families ==1 <=z', {'max_families': 1, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages families >=1 >=a', {'min_families': 2, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages families >=1 <=z', {'min_families': 2, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages families ==2 >=a', {'min_families': 2, 'max_families': 2, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages families ==2 <=z', {'min_families': 2, 'max_families': 2, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages families ==5 >=a', {'min_families': 5, 'max_families': 5, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages families ==5 <=z', {'min_families': 5, 'max_families': 5, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages families >=5 >=a', {'min_families': 5, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages families >=5 <=z', {'min_families': 5, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages families >=25 >=a', {'min_families': 25, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages families >=25 <=z', {'min_families': 25, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer >=a', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer <=z', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer newest >=a', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'newest': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer newest <=z', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'newest': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer outdated >=a', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'outdated': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer outdated <=z', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'outdated': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer problematic >=a', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'problematic': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo maintainer problematic <=z', {'inrepo': 'freebsd', 'maintainer': 'amdmi3@freebsd.org', 'problematic': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo newest 1r >=a', {'inrepo': 'freebsd', 'max_repos_newest': 1, 'newest': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo newest 1r <=z', {'inrepo': 'freebsd', 'max_repos_newest': 1, 'newest': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo newest 1f >=a', {'inrepo': 'freebsd', 'max_families_newest': 1, 'newest': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo newest 1f <=z', {'inrepo': 'freebsd', 'max_families_newest': 1, 'newest': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages repo related >=a', {'inrepo': 'freebsd', 'has_related': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages repo related <=z', {'inrepo': 'freebsd', 'has_related': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages maint related >=a', {'maintainer': 'amdmi3@freebsd.org', 'has_related': True, 'pivot': 'a', 'limit': 200}),
    ('query_metapackages', 'metapackages maint related <=z', {'maintainer': 'amdmi3@freebsd.org', 'has_related': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('query_metapackages', 'metapackages maint related <=z', {'maintainer': 'amdmi3@freebsd.org', 'has_related': True, 'pivot': 'z', 'reverse': True, 'limit': 200}),
    ('get_maintainer_similar_maintainers', 'maintainer similar', {'maintainer': 'amdmi3@freebsd.org', 'limit': 200}),
    ('get_metapackage_related_metapackages', 'metapackage related small', {'effname': 'firefox', 'limit': 200}),
    ('get_metapackage_related_metapackages', 'metapackage related big', {'effname': 'gnumeric', 'limit': 200}),
]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-D', '--dsn', default=config['DSN'], help='database connection params')
    parser.add_argument('-Q', '--sql-dir', default=config['SQL_DIR'], help='path to directory with sql queries')

    parser.add_argument('-t', '--min-time', type=float, default=0.0, help='min time in seconds for testing each query')
    parser.add_argument('-i', '--min-iterations', type=int, default=1, help='min iterations for testing each query')
    parser.add_argument('-e', '--epsilon', type=float, default=0.01, help='ignore difference below this threshold')

    parser.add_argument('-l', '--load', type=str, help='compare to results from previously saved data file')
    parser.add_argument('-s', '--save', type=str, help='save results to a data file')

    parser.add_argument('-x', '--explain', action='store_true', help='print query explains')

    parser.add_argument('keywords', metavar='keyword', nargs='*', help='keywords to filter queries by')

    return parser.parse_args()


def run_single_query(database: Database, method: str, kwargs: Any, options: argparse.Namespace) -> float:
    mindelta: Optional[float] = None
    totaldelta = 0.0
    iteration = 0

    query = getattr(database, method)
    while totaldelta < options.min_time or iteration < options.min_iterations:
        start = time.monotonic()

        query(**kwargs)
        delta = time.monotonic() - start

        if mindelta is None or delta < mindelta:
            mindelta = delta

        totaldelta += delta
        iteration += 1

    if options.explain:
        explain_query = getattr(database, 'explain_' + method)
        print(explain_query(**kwargs), file=sys.stderr)

    assert(mindelta is not None)
    return mindelta


def check_keywords(name: str, keywords: List[str]) -> bool:
    if not keywords:
        return True

    for keyword in keywords:
        if keyword in name:
            return True

    return False


def main() -> int:
    options = parse_arguments()

    querymgr = QueryManager(options.sql_dir)
    database = Database(options.dsn, querymgr, readonly=True, application_name='repology-benchmark')

    reference: Dict[str, float] = {}
    if options.load:
        try:
            with open(options.load, 'rb') as reffile:
                reference = pickle.load(reffile)
        except:
            pass

    results = []
    for num, (method, name, kwargs) in enumerate(queries):
        if not check_keywords(name, options.keywords):
            continue
        print('===> {}/{}: "{}"\n'.format(num + 1, len(queries), name), file=sys.stderr, end='')
        results.append((name, run_single_query(database, method, kwargs, options)))
        sys.stderr.flush()

    for name, delta in results:
        change = ''
        if name in reference:
            if max(delta, reference[name]) / min(delta, reference[name]) < (1 + options.epsilon):
                change = ' no change'
            elif delta > reference[name]:
                change = ' \033[0;91m{:.1f}% slower\033[0m'.format(100.0 * delta / reference[name] - 100.0)
            else:
                change = ' \033[0;92m{:.1f}% faster\033[0m'.format(100.0 * reference[name] / delta - 100.0)

            change += ' (was {:.2f}ms)'.format(reference[name] * 1000.0)

        print('{:>50s} {:.2f}ms{}'.format(name, delta * 1000.0, change), file=sys.stderr)

    if options.save:
        reference = {
            name: delta for name, delta in results
        }
        with open(options.save, 'wb') as reffile:
            pickle.dump(reference, reffile)

    return 0


if __name__ == '__main__':
    sys.exit(main())
