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

import flask

from repology.package import VersionClass
from repology.packageproc import PackagesetSortByVersions
from repology.queryfilters import NameAfterQueryFilter, NameBeforeQueryFilter, NameStartingQueryFilter


def bound_to_filter(bound):
    if bound and bound.startswith('<'):
        return NameBeforeQueryFilter(bound[1:])
    elif bound and bound.startswith('>'):
        return NameAfterQueryFilter(bound[1:])
    else:
        return NameStartingQueryFilter(bound)


def get_packages_name_range(packages):
    firstname, lastname = None, None

    if packages:
        firstname = lastname = packages[0].effname
        for package in packages[1:]:
            lastname = max(lastname, package.effname)
            firstname = min(firstname, package.effname)

    return firstname, lastname


def metapackages_to_summary_items(metapackages, repo=None, maintainer=None):
    metapackagedata = {}

    for metapackagename, packages in metapackages.items():
        # we gather two kinds of statistics: one is for explicitly requested
        # subset of packages (e.g. ones belonging to specified repo or maintainer)
        # and a general one for all other packages
        summaries = {
            sumtype: {
                'keys': [],
                'families_by_key': {}
            } for sumtype in ['explicit', 'newest', 'outdated', 'ignored']
        }

        families = set()

        # gather summaries
        for package in PackagesetSortByVersions(packages):
            families.add(package.family)

            key = (package.version, package.versionclass)
            target = None

            if (repo is not None and repo == package.repo) or (maintainer is not None and maintainer in package.maintainers):
                target = summaries['explicit']
            elif package.versionclass in [VersionClass.outdated, VersionClass.legacy]:
                target = summaries['outdated']
                key = (package.version, VersionClass.outdated)  # we don't to distinguish legacy here
            elif package.versionclass in [VersionClass.devel, VersionClass.newest, VersionClass.unique]:
                target = summaries['newest']
            else:
                target = summaries['ignored']

            if key not in target['families_by_key']:
                target['keys'].append(key)

            target['families_by_key'].setdefault(key, set()).add(package.family)

        # convert summaries
        for sumtype, summary in summaries.items():
            summaries[sumtype] = [
                {
                    'version': key[0],
                    'versionclass': key[1],
                    'families': summary['families_by_key'][key]
                } for key in summary['keys']
            ]

        metapackagedata[metapackagename] = {
            'families': families,
            **summaries
        }

    return metapackagedata
