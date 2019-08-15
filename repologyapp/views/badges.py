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

import re
from collections import defaultdict
from functools import cmp_to_key
from typing import Any

import flask

from libversion import version_compare

from repologyapp.badges import BadgeCell, badge_color, render_generic_badge
from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.packageproc import packageset_to_best_by_repo
from repologyapp.view_registry import ViewRegistrar

from repology.package import PackageStatus


@ViewRegistrar('/badge/vertical-allrepos/<name>.svg')
def badge_vertical_allrepos(name: str) -> Any:
    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = packageset_to_best_by_repo(packages)

    args = flask.request.args.to_dict()

    header = args.get('header')
    minversion = args.get('minversion')

    cells = []

    for reponame in repometadata.active_names():
        if reponame in best_pkg_by_repo:
            version = best_pkg_by_repo[reponame].version
            versionclass = best_pkg_by_repo[reponame].versionclass
            unsatisfying = minversion and version_compare(version, minversion) < 0

            color = badge_color(versionclass, unsatisfying)

            cells.append([
                BadgeCell(repometadata[reponame]['desc'], align='r'),
                BadgeCell(version, color=color, truncate=13, minwidth=60)
            ])

    if header is None:
        header = 'Packaging status' if cells else 'No known packages'

    return render_generic_badge(cells, header=header)


@ViewRegistrar('/badge/tiny-repos/<name>.svg')
def badge_tiny_repos(name: str) -> Any:
    return render_generic_badge([[
        BadgeCell(flask.request.args.to_dict().get('header', 'in repositories'), collapsible=True),
        BadgeCell(str(get_db().get_metapackage_families_count(name)), '#007ec6'),
    ]])


@ViewRegistrar('/badge/version-for-repo/<repo>/<name>.svg')
def badge_version_for_repo(repo: str, name: str) -> Any:
    if repo not in repometadata.all_names():
        flask.abort(404)

    packages = get_db().get_metapackage_packages(name, fields=['repo', 'version', 'versionclass'])
    best_pkg_by_repo = packageset_to_best_by_repo(packages)

    left_cell = BadgeCell(flask.request.args.to_dict().get('header', repometadata[repo]['singular']), collapsible=True)

    if repo not in best_pkg_by_repo:
        # Note: it would be more correct to return 404 with content here,
        # but some browsers (e.g. Firefox) won't display the image in that case
        right_cell = BadgeCell('-')
    else:
        version = best_pkg_by_repo[repo].version
        versionclass = best_pkg_by_repo[repo].versionclass

        minversion = flask.request.args.to_dict().get('minversion')
        unsatisfying = minversion and version_compare(version, minversion) < 0

        right_cell = BadgeCell(version, badge_color(versionclass, unsatisfying), truncate=20)

    return render_generic_badge([[left_cell, right_cell]])


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

    return render_generic_badge([[
        BadgeCell(caption, collapsible=True),
        BadgeCell(text, '#007ec6'),
    ]])


@ViewRegistrar('/badge/versions-matrix.svg')
def badge_versions_matrix() -> Any:
    args = flask.request.args.to_dict()

    header = args.get('header')

    # parse requirements
    required_projects = {}

    for project in args.get('projects', '').split(','):
        match = re.fullmatch('(.*?)(>=?|<=?)(.*?)', project)
        if match is not None:
            required_projects[match.group(1)] = (match.group(2), match.group(3))
        else:
            required_projects[project] = None

    required_repos = set(args.get('repos').split(',')) if 'repos' in args else None

    require_all = args.get('require_all', False)

    # get and process packages
    packages = get_db().get_metapackages_packages(list(required_projects.keys()), fields=['effname', 'repo', 'version', 'versionclass'])

    packages_by_project = defaultdict(list)
    repos = set()
    for package in packages:
        packages_by_project[package.effname].append(package)
        repos.add(package.repo)

    best_packages_by_project = {effname: packageset_to_best_by_repo(packages) for effname, packages in packages_by_project.items()}

    if required_repos is not None:
        repos = repos & required_repos

    # construct table
    cells = [[BadgeCell()]]

    for name in required_projects.keys():
        cells[0].append(BadgeCell(name))

    for repo in repometadata.sorted_active_names(repos):
        row = [BadgeCell(repometadata[repo]['desc'], align='r')]

        for effname, restriction in required_projects.items():
            if effname not in best_packages_by_project or repo not in best_packages_by_project[effname]:
                # project not found in repo
                row.append(BadgeCell('-'))

                if require_all:
                    break
                else:
                    continue

            package = best_packages_by_project[effname][repo]
            unsatisfying = False

            if restriction is not None:
                if restriction[0] == '>':
                    unsatisfying = version_compare(package.version, restriction[1]) <= 0
                elif restriction[0] == '>=':
                    unsatisfying = version_compare(package.version, restriction[1]) < 0
                elif restriction[0] == '<':
                    unsatisfying = version_compare(package.version, restriction[1]) >= 0
                elif restriction[0] == '<=':
                    unsatisfying = version_compare(package.version, restriction[1]) > 0

            color = badge_color(package.versionclass, unsatisfying)

            row.append(BadgeCell(package.version, color=color, truncate=13, minwidth=60))
        else:
            cells.append(row)

    return render_generic_badge(cells, header=header)
