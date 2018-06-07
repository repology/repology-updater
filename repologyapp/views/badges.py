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

from functools import cmp_to_key

import flask

from libversion import version_compare

from repologyapp.globals import *
from repologyapp.view_registry import ViewRegistrar

from repology.package import VersionClass
from repology.packageproc import PackagesetToBestByRepo


@ViewRegistrar('/badge/vertical-allrepos/<name>.svg')
def badge_vertical_allrepos(name):
    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = PackagesetToBestByRepo(packages)

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
    return (
        flask.render_template(
            'badge-tiny-blue.svg',
            name=name,
            caption='in repositories',
            text=get_db().get_metapackage_families_count(name)
        ),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/version-for-repo/<repo>/<name>.svg')
def badge_version_for_repo(repo, name):
    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = PackagesetToBestByRepo(packages)

    if repo not in best_pkg_by_repo:
        # XXX: display this as normal "pill" badge with correct repository name
        return (
            flask.render_template('badge-tiny-string.svg', string='No package'),
            # XXX: it's more correct to return 404 with content
            # here, but some browsers (e.g. Firefox) won't display
            # the image in that case
            {'Content-type': 'image/svg+xml'}
        )

    return (
        flask.render_template(
            'badge-tiny-version.svg',
            repo=repo,
            version=best_pkg_by_repo[repo].version,
            versionclass=best_pkg_by_repo[repo].versionclass,
        ),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/version-only-for-repo/<repo>/<name>.svg')
def badge_version_only_for_repo(repo, name):
    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = PackagesetToBestByRepo(packages)

    if repo not in best_pkg_by_repo:
        return (
            flask.render_template('badge-tiny-string.svg', string='-'),
            # XXX: it's more correct to return 404 with content
            # here, but some browsers (e.g. Firefox) won't display
            # the image in that case
            {'Content-type': 'image/svg+xml'}
        )

    return (
        flask.render_template(
            'badge-tiny-version-only.svg',
            repo=repo,
            version=best_pkg_by_repo[repo].version,
            versionclass=best_pkg_by_repo[repo].versionclass,
        ),
        {'Content-type': 'image/svg+xml'}
    )


@ViewRegistrar('/badge/latest-versions/<name>.svg')
def badge_latest_versions(name):
    def version_compare_rev(v1, v2):
        return version_compare(v2, v1)

    versions = sorted(set([
        package.version
        for package in get_db().get_metapackage_packages(name, fields=['version', 'versionclass'])
        if package.versionclass in (VersionClass.newest, VersionClass.devel, VersionClass.unique)
    ]), key=cmp_to_key(version_compare_rev))

    caption = 'latest packaged version'

    if versions:
        if len(versions) > 1:
            caption += 's'
        versions = ', '.join(versions)
    else:
        versions = '-'

    return (
        flask.render_template(
            'badge-tiny-blue.svg',
            name=name,
            caption=caption,
            text=versions
        ),
        {'Content-type': 'image/svg+xml'}
    )
