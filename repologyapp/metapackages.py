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

from repologyapp.metapackage_request import MetapackageRequest
from repologyapp.version import UserVisibleVersionInfo

from repology.package import VersionClass


class MetapackagesFilterInfo:
    fields = {
        'search': {
            'type': str,
            'advanced': False,
            'action': lambda request, value: request.NameSubstring(value.strip().lower()),
        },
        'package': {
            'type': str,
            'advanced': True,
            'action': lambda request, value: request.Package(value.strip()),
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

    sumtypes = ('explicit', 'newest', 'outdated', 'ignored')

    def summary_factory():
        return {
            sumtype: defaultdict(set)
            for sumtype in sumtypes
        }

    summaries = defaultdict(summary_factory)

    # pass 1: gather summaries in the intermediate format:
    # dict by metapackage name -> dict by summary type (e.g. table columns) -> hash by versioninfo of sets of families
    for package in packages:
        target = None

        versioninfo = UserVisibleVersionInfo(package)

        if (repo is not None and repo == package.repo) or (maintainer is not None and maintainer in package.maintainers):
            target = summaries[package.effname]['explicit']
        elif package.versionclass in [VersionClass.outdated, VersionClass.legacy]:
            target = summaries[package.effname]['outdated']
            versioninfo.versionclass = VersionClass.outdated  # we don't need to differentiate legacy and outdated here
        elif package.versionclass in [VersionClass.devel, VersionClass.newest, VersionClass.unique]:
            target = summaries[package.effname]['newest']
        else:
            target = summaries[package.effname]['ignored']

        target[versioninfo].add(package.family)

    # pass 2: count families and convert to final format:
    # dict by metapackage name -> dict by summary type (e.g. table columns) -> list of versioninfos (with filled spread)
    for summary in summaries.values():
        for sumtype in sumtypes:
            summary[sumtype] = sorted([
                versioninfo.as_with_spread(len(families)) for versioninfo, families in summary[sumtype].items()
            ], reverse=True)

    return summaries


def packages_to_metapackages(*packagesets):
    metapackages = defaultdict(list)

    for packages in packagesets:
        for package in packages:
            metapackages[package.effname].append(package)

    return metapackages
