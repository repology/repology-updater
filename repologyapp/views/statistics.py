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

import flask

from repologyapp.globals import *
from repologyapp.math import safe_percent
from repologyapp.view_registry import ViewRegistrar

from repology.config import config


@ViewRegistrar('/statistics')
@ViewRegistrar('/statistics/<sorting>')
def statistics(sorting=None):
    repostats = {repostat['name']: repostat for repostat in get_db().GetRepositories()}
    repostats = [repostats[reponame] for reponame in reponames if reponame in repostats]
    showmedals = True

    if sorting == 'newest':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_newest'], reverse=True)
    elif sorting == 'pnewest':
        repostats = sorted(repostats, key=lambda s: safe_percent(s['num_metapackages_newest'], s['num_metapackages'] - s['num_metapackages_unique']), reverse=True)
    elif sorting == 'outdated':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_outdated'], reverse=True)
    elif sorting == 'poutdated':
        repostats = sorted(repostats, key=lambda s: safe_percent(s['num_metapackages_outdated'], s['num_metapackages'] - s['num_metapackages_unique']), reverse=True)
    elif sorting == 'total':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages'], reverse=True)
    else:
        sorting = 'name'
        showmedals = False

    return flask.render_template(
        'statistics.html',
        sorting=sorting,
        repostats=repostats,
        showmedals=showmedals,
        repostats_old={},  # {repo['name']: repo for repo in get_db().GetRepositoriesHistoryAgo(60 * 60 * 24 * 7)},
        num_metapackages=get_db().GetMetapackagesCount()
    )
