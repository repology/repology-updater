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

from collections import defaultdict

import flask

from repology.database import MetapackageRequest
from repology.package import VersionClass


class MetapackagesFilterInfo:
    fields = {
        'search': {
            'type': str,
            'advanced': False,
            'action': lambda request, value: request.NameSubstring(value.strip().lower()),
        },
        'maintainer': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.Maintainer(value.strip().lower()),
        },
        'category': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.Category(value.strip()),  # case sensitive (yet)
        },
        'inrepo': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.InRepo(value.strip().lower()),
        },
        'notinrepo': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.NotInRepo(value.strip().lower()),
        },
        'repos': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.Repos(value),
        },
        'families': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.Families(value),
        },
        'repos_newest': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.ReposNewest(value),
        },
        'families_newest': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.FamiliesNewest(value),
        },
        'newest': {
            'type': bool,
            'advanced': True,
            'action': lambda request, value: request.Newest(),
        },
        'outdated': {
            'type': bool,
            'advanced': True,
            'action': lambda request, value: request.Outdated(),
        },
        'problematic': {
            'type': bool,
            'advanced': True,
            'action': lambda request, value: request.Problematic(),
        },
        'has_related': {
            'type': bool,
            'advanced': True,
            'action': lambda request, value: request.HasRelated(),
        },
    }

    def __init__(self):
        self.args = {}

    def ParseFlaskArgs(self):
        flask_args = flask.request.args.to_dict()

        for fieldname, fieldinfo in MetapackagesFilterInfo.fields.items():
            if fieldname in flask_args:
                if fieldinfo['type'] == bool:
                    self.args[fieldname] = True
                elif fieldinfo['type'] == int and flask_args[fieldname].isdecimal():
                    self.args[fieldname] = int(flask_args[fieldname])
                elif fieldinfo['type'] == str and flask_args[fieldname]:
                    self.args[fieldname] = flask_args[fieldname]

    def GetDict(self):
        return self.args

    def GetRequest(self):
        request = MetapackageRequest()
        for fieldname, fieldinfo in MetapackagesFilterInfo.fields.items():
            if fieldname in self.args:
                fieldinfo['action'](request, self.args[fieldname])

        return request

    def GetMaintainer(self):
        return self.args['maintainer'] if 'maintainer' in self.args else None

    def GetRepo(self):
        return self.args['inrepo'] if 'inrepo' in self.args else None

    def IsAdvanced(self):
        for fieldname in self.args.keys():
            if MetapackagesFilterInfo.fields[fieldname]['advanced']:
                return True
        return False


def get_packages_name_range(packages):
    firstname, lastname = None, None

    if packages:
        firstname = lastname = packages[0].effname
        for package in packages[1:]:
            lastname = max(lastname, package.effname)
            firstname = min(firstname, package.effname)

    return firstname, lastname


def packages_to_summary_items(packages, repo=None, maintainer=None):
    # filter by either repo or maintainer, not both
    if repo is not None:
        maintainer = None

    def summary_factory():
        return {
            sumtype: []
            for sumtype in ['explicit', 'newest', 'outdated', 'ignored']
        }

    # pass1: gather packages under summaries[<effname>][<explicit|newest|outdated|ignored>]
    summaries = defaultdict(summary_factory)

    for package in packages:
        target = None

        if (repo is not None and repo == package.repo) or (maintainer is not None and maintainer in package.maintainers):
            target = summaries[package.effname]['explicit']
        elif package.versionclass in [VersionClass.outdated, VersionClass.legacy]:
            target = summaries[package.effname]['outdated']
        elif package.versionclass in [VersionClass.devel, VersionClass.newest, VersionClass.unique]:
            target = summaries[package.effname]['newest']
        else:
            target = summaries[package.effname]['ignored']

        target.append(package)

    # pass2: convert package lists into lists of version infos
    def condense_version_families(tuples):
        if not tuples:
            return

        current_key = tuples[0][0]
        current_values = set([tuples[0][1]])

        for key, value in tuples[1:]:
            if key != current_key:
                yield (current_key, len(current_values))
                current_key = key
                current_values = set()

            current_values.add(value)

        yield (current_key, len(current_values))

    final_summaries = defaultdict(summary_factory)

    for metapackagename, summary in summaries.items():
        for sumtype, packages in summary.items():
            final_summaries[metapackagename][sumtype] = list(
                condense_version_families(
                    sorted(
                        [
                            (package.get_user_visible_version().flatten_legacy(), package.family)
                            for package in packages
                        ],
                        reverse=True
                    )
                )
            )

    return final_summaries


def packages_to_metapackages(*packagesets):
    metapackages = defaultdict(list)

    for packages in packagesets:
        for package in packages:
            metapackages[package.effname].append(package)

    return metapackages
