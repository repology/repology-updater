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
from repologyapp.view_registry import ViewRegistrar

from repology.config import config
from repology.packageproc import PackagesetToBestByRepo


@ViewRegistrar('/badge/vertical-allrepos/<name>.svg')
def badge_vertical_allrepos(name):
    best_pkg_by_repo = PackagesetToBestByRepo(get_db().GetMetapackage(name))

    entries = [
        {
            'repo': repometadata[reponame],
            'package': best_pkg_by_repo[reponame]
        } for reponame in reponames if reponame in repometadata and reponame in best_pkg_by_repo
    ]

    return (
        flask.render_template(
            'badge-vertical.svg',
            entries=entries,
            name=name
        ),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/tiny-repos/<name>.svg')
def badge_tiny_repos(name):
    num_families = len(set([package.family for package in get_db().GetMetapackage(name)]))
    return (
        flask.render_template(
            'badge-tiny.svg',
            name=name,
            num_families=num_families
        ),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/version-for-repo/<repo>/<name>.svg')
def badge_version_for_repo(repo, name):
    best_pkg_by_repo = PackagesetToBestByRepo(get_db().GetMetapackage(name))

    if repo not in best_pkg_by_repo:
        flask.abort(404)

    return (
        flask.render_template(
            'badge-tiny-version.svg',
            repo=repo,
            version=best_pkg_by_repo[repo].version,
            versionclass=best_pkg_by_repo[repo].versionclass,
        ),
        {'Content-type': 'image/svg+xml'}
    )
