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

import datetime
from typing import Any, Optional

import flask

from repologyapp.config import config
from repologyapp.db import get_db
from repologyapp.feed_helpers import smear_timestamps
from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/maintainers/')
@ViewRegistrar('/maintainers/<bound>/')
def maintainers(bound: Optional[str] = None) -> Any:
    reverse = False
    if bound and bound.startswith('..'):
        bound = bound[2:]
        reverse = True
    elif bound and bound.endswith('..'):
        bound = bound[:-2]

    search = flask.request.args.to_dict().get('search')
    search = None if search is None else search.strip().lower()

    minmaintainer, maxmaintainer = get_db().get_maintainers_range()

    maintainers = get_db().query_maintainers(bound, reverse, search, config['MAINTAINERS_PER_PAGE'])

    firstpage, lastpage = False, False
    for maintainer in maintainers:
        if maintainer['maintainer'] == minmaintainer:
            firstpage = True
        if maintainer['maintainer'] == maxmaintainer:
            lastpage = True

    return flask.render_template(
        'maintainers.html',
        search=search,
        minmaintainer=minmaintainer,
        maxmaintainer=maxmaintainer,
        firstpage=firstpage,
        lastpage=lastpage,
        maintainers=maintainers
    )


@ViewRegistrar('/maintainer/<maintainer>')
def maintainer(maintainer: str) -> Any:
    maintainer = maintainer.lower()

    maintainer_info = get_db().get_maintainer_information(maintainer)

    if not maintainer_info:
        return (flask.render_template('maintainer-404.html', maintainer=maintainer, maintainer_info=maintainer_info), 404)
    elif maintainer_info['num_packages'] == 0:
        # HTTP code is intentionally 404
        return (flask.render_template('maintainer-410.html', maintainer=maintainer, maintainer_info=maintainer_info), 404)

    metapackages = get_db().get_maintainer_metapackages(maintainer, 500)
    similar_maintainers = get_db().get_maintainer_similar_maintainers(maintainer, 50)
    numproblems = get_db().get_maintainer_problems_count(maintainer)

    for key in ('repository_package_counts', 'repository_metapackage_counts', 'category_metapackage_counts'):
        if maintainer_info[key]:
            maintainer_info[key] = [
                (num, name)
                for name, num in maintainer_info[key].items()
            ]

    return flask.render_template(
        'maintainer.html',
        numproblems=numproblems,
        maintainer=maintainer,
        maintainer_info=maintainer_info,
        metapackages=metapackages,
        similar_maintainers=similar_maintainers
    )


@ViewRegistrar('/maintainer/<maintainer>/problems')
def maintainer_problems(maintainer: str) -> Any:
    maintainer = maintainer.lower()

    return flask.render_template(
        'maintainer-problems.html',
        maintainer=maintainer,
        problems=get_db().get_maintainer_problems(
            maintainer,
            config['PROBLEMS_PER_PAGE']
        )
    )


@ViewRegistrar('/maintainer/<maintainer>/feed-for-repo/<repo>')
def maintainer_repo_feed(maintainer: str, repo: str) -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    return flask.render_template(
        'maintainer-repo-feed.html',
        maintainer=maintainer,
        repo=repo,
        history=smear_timestamps(
            get_db().get_maintainer_feed(
                maintainer=maintainer,
                repo=repo,
                limit=config['HISTORY_PER_PAGE']
            )
        ),
        autorefresh=autorefresh
    )


@ViewRegistrar('/maintainer/<maintainer>/feed-for-repo/<repo>/atom')
def maintainer_repo_feed_atom(maintainer: str, repo: str) -> Any:
    return (
        flask.render_template(
            'maintainer-repo-feed-atom.xml',
            maintainer=maintainer,
            repo=repo,
            history=smear_timestamps(
                get_db().get_maintainer_feed(
                    maintainer=maintainer,
                    repo=repo,
                    timespan=datetime.timedelta(weeks=4),
                    limit=config['HISTORY_PER_PAGE']
                )
            )
        ),
        {'Content-type': 'application/atom+xml'}
    )
