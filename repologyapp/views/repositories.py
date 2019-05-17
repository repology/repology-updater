# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any, Optional

import flask

from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.math import safe_percent
from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/repositories/statistics')
@ViewRegistrar('/repositories/statistics/<sorting>')
def repositories_statistics(sorting: Optional[str] = None) -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    repostats_by_name = {repostat['name']: repostat for repostat in get_db().get_active_repositories()}
    repostats = [repostats_by_name[reponame] for reponame in repometadata.active_names() if reponame in repostats_by_name]
    showmedals = True

    if sorting == 'newest':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_newest'], reverse=True)
    elif sorting == 'pnewest':
        repostats = sorted(repostats, key=lambda s: safe_percent(s['num_metapackages_newest'], s['num_metapackages_comparable']), reverse=True)
    elif sorting == 'outdated':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_outdated'], reverse=True)
    elif sorting == 'poutdated':
        repostats = sorted(repostats, key=lambda s: safe_percent(s['num_metapackages_outdated'], s['num_metapackages_comparable']), reverse=True)
    elif sorting == 'total':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages'], reverse=True)
    elif sorting == 'nonunique':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages'] - s['num_metapackages_unique'], reverse=True)
    else:
        sorting = 'name'
        showmedals = False

    return flask.render_template(
        'repositories-statistics.html',
        sorting=sorting,
        repostats=repostats,
        showmedals=showmedals,
        repostats_old={},  # {repo['name']: repo for repo in get_db().GetRepositoriesHistoryAgo(60 * 60 * 24 * 7)},
        counts=get_db().get_counts(),
        autorefresh=autorefresh
    )


@ViewRegistrar('/repositories/packages')
def repositories_packages() -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    repostats_by_name = {repostat['name']: repostat for repostat in get_db().get_active_repositories()}
    repostats = [repostats_by_name[reponame] for reponame in repometadata.active_names() if reponame in repostats_by_name]

    return flask.render_template(
        'repositories-packages.html',
        repostats=repostats,
        counts=get_db().get_counts(),
        autorefresh=autorefresh
    )


@ViewRegistrar('/repositories/updates')
def repositories_updates() -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    return flask.render_template(
        'repositories-updates.html',
        repos=get_db().get_repositories_update_statistics(),
        autorefresh=autorefresh
    )


@ViewRegistrar('/repositories/graphs')
def repositories_graphs() -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    return flask.render_template(
        'repositories-graphs.html',
        autorefresh=autorefresh
    )
