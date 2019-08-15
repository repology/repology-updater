# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from functools import cmp_to_key
from typing import Any

import flask

from libversion import version_compare

from repologyapp.badges import TinyBadgeRenderer
from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.packageproc import packageset_to_best_by_repo
from repologyapp.view_registry import ViewRegistrar

from repology.package import PackageStatus


@ViewRegistrar('/badge/vertical-allrepos/<name>.svg')
def badge_vertical_allrepos(name: str) -> Any:
    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = packageset_to_best_by_repo(packages)

    header = flask.request.args.to_dict().get('header', 'Packaging status')
    minversion = flask.request.args.to_dict().get('minversion')

    entries = [
        {
            'repo': repometadata[reponame],
            'package': best_pkg_by_repo[reponame],
            'unsatisfying': version_compare(best_pkg_by_repo[reponame].version, minversion) < 0 if minversion else False,
        } for reponame in repometadata.active_names() if reponame in best_pkg_by_repo
    ]

    if not entries:
        header = 'No known packages'

    return (
        flask.render_template(
            'badge-vertical.svg',
            entries=entries,
            name=name,
            header=header
        ),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/tiny-repos/<name>.svg')
def badge_tiny_repos(name: str) -> Any:
    badge = TinyBadgeRenderer()
    badge.add_section(flask.request.args.to_dict().get('header', 'in repositories'))
    badge.add_section(get_db().get_metapackage_families_count(name), '#007ec6')

    return (
        badge.render(),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/version-for-repo/<repo>/<name>.svg')
def badge_version_for_repo(repo: str, name: str) -> Any:
    if repo not in repometadata.all_names():
        flask.abort(404)

    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = packageset_to_best_by_repo(packages)

    badge = TinyBadgeRenderer()
    badge.add_section(flask.request.args.to_dict().get('header', repometadata[repo]['singular']))

    if repo not in best_pkg_by_repo:
        # Note: it would be more correct to return 404 with content here,
        # but some browsers (e.g. Firefox) won't display the image in that case
        badge.add_section('-')
    else:
        version = best_pkg_by_repo[repo].version
        versionclass = best_pkg_by_repo[repo].versionclass

        minversion = flask.request.args.to_dict().get('minversion')

        if minversion and version_compare(version, minversion) < 0:
            color = '#e00000'
        elif versionclass in [PackageStatus.OUTDATED, PackageStatus.LEGACY]:
            color = '#e05d44'
        elif versionclass in [PackageStatus.NEWEST, PackageStatus.UNIQUE, PackageStatus.DEVEL]:
            color = '#4c1'
        else:
            color = '#9f9f9f'

        badge.add_section(version, color)

    return (
        badge.render(),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/latest-versions/<name>.svg')
def badge_latest_versions(name: str) -> Any:
    versions = sorted(set((
        package.version
        for package in get_db().get_metapackage_packages(name, fields=['version', 'versionclass'])
        if package.versionclass in (PackageStatus.NEWEST, PackageStatus.DEVEL, PackageStatus.UNIQUE)
    )), key=cmp_to_key(version_compare), reverse=True)

    default_caption = 'latest packaged version'

    if len(versions) > 1:
        default_caption += 's'
        text = ', '.join(versions)
    elif versions:
        text = versions[0]
    else:
        text = '-'

    caption = flask.request.args.to_dict().get('header', default_caption)

    badge = TinyBadgeRenderer()
    badge.add_section(caption)
    badge.add_section(text, '#007ec6')

    return (
        badge.render(),
        {'Content-type': 'image/svg+xml'}
    )
