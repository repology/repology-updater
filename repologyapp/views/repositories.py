# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
# Copyright (C) 2018 Paul Wise <pabs3@bonedaddy.net>
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

from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.math import safe_percent
from repologyapp.view_registry import ViewRegistrar
from werkzeug.routing import BuildError


@ViewRegistrar('/repositories/statistics')
@ViewRegistrar('/repositories/statistics/<sorting>')
def repositories_statistics(sorting=None):
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    repostats = {repostat['name']: repostat for repostat in get_db().get_active_repositories()}
    repostats = [repostats[reponame] for reponame in repometadata.active_names() if reponame in repostats]
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
def repositories_packages():
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    repostats = {repostat['name']: repostat for repostat in get_db().get_active_repositories()}
    repostats = [repostats[reponame] for reponame in repometadata.active_names() if reponame in repostats]

    return flask.render_template(
        'repositories-packages.html',
        repostats=repostats,
        counts=get_db().get_counts(),
        autorefresh=autorefresh
    )


@ViewRegistrar('/repositories/updates')
def repositories_updates():
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    return flask.render_template(
        'repositories-updates.html',
        repos=get_db().get_repositories_update_statistics(),
        autorefresh=autorefresh
    )


@ViewRegistrar('/repositories/graphs')
def repositories_graphs():
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    return flask.render_template(
        'repositories-graphs.html',
        autorefresh=autorefresh
    )


@ViewRegistrar('/repository/<repo>/package/<package>/problems')
def package_problems(repo, package):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.render_template('package-problems.html', repo=repo, package=package, problems=get_db().get_package_problems(repo, package, config['PROBLEMS_PER_PAGE']))


@ViewRegistrar('/repository/<repo>/package/<package>/<page>')
def package_metapackage(repo, package, page=None):
    if not repo or repo not in repometadata or not package:
        flask.abort(404)

    metapackages = get_db().get_package_metapackage(package)
    metapackage_count = len(metapackages)

    if metapackage_count == 0:
        flask.abort(404)
    elif metapackage_count == 1:
        page_base = 'metapackage'
        if page:
            page = '_' + page
        else:
            page = ''
        page_type = page_base + page
        metapackage = metapackages[0]
        try:
            url = flask.url_for(page_type, name=metapackage)
        except BuildError:
            flask.abort(404)
    else:
        url = flask.url_for('metapackages', repo=repo, package=package)
    return flask.redirect(url, 307)
