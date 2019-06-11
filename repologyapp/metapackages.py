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

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import flask

from repologyapp.metapackage_request import MetapackageRequest
from repologyapp.version import UserVisibleVersionInfo

from repology.package import Package, PackageStatus


class MetapackagesFilterInfo:
    @dataclass
    class _FieldDescriptor:
        argtype: Any
        advanced: bool
        action: Callable[[MetapackageRequest, Any], None]

    _fields: Dict[str, _FieldDescriptor] = {
        'search': _FieldDescriptor(
            str,
            False,
            lambda request, value: request.require_name_substring(value.strip().lower()),
        ),
        'maintainer': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_maintainer(value.strip().lower()),
        ),
        'category': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_category(value.strip()),  # case sensitive (yet)
        ),
        'inrepo': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_in_repo(value.strip().lower()),
        ),
        'notinrepo': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_not_in_repo(value.strip().lower()),
        ),
        'repos': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_repos(value),
        ),
        'families': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_families(value),
        ),
        'repos_newest': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_repos_newest(value),
        ),
        'families_newest': _FieldDescriptor(
            str,
            True,
            lambda request, value: request.require_families_newest(value),
        ),
        'newest': _FieldDescriptor(
            bool,
            True,
            lambda request, value: request.require_newest(),
        ),
        'outdated': _FieldDescriptor(
            bool,
            True,
            lambda request, value: request.require_outdated(),
        ),
        'problematic': _FieldDescriptor(
            bool,
            True,
            lambda request, value: request.require_problematic(),
        ),
        'has_related': _FieldDescriptor(
            bool,
            True,
            lambda request, value: request.require_has_related(),
        ),
    }

    _args: Dict[str, Any]

    def __init__(self) -> None:
        self._args = {}

    def parse_flask_args(self) -> None:
        flask_args = flask.request.args.to_dict()

        for fieldname, fielddesc in MetapackagesFilterInfo._fields.items():
            if fieldname in flask_args:
                if fielddesc.argtype is bool:
                    self._args[fieldname] = True
                elif fielddesc.argtype is int and flask_args[fieldname].isdecimal():
                    self._args[fieldname] = int(flask_args[fieldname])
                elif fielddesc.argtype is str and flask_args[fieldname]:
                    self._args[fieldname] = flask_args[fieldname]

    def get_dict(self) -> Dict[str, Any]:
        return self._args

    def get_request(self) -> MetapackageRequest:
        request = MetapackageRequest()
        for fieldname, fielddesc in MetapackagesFilterInfo._fields.items():
            if fieldname in self._args:
                fielddesc.action(request, self._args[fieldname])  # type: ignore

        return request

    def get_maintainer(self) -> Optional[str]:
        return self._args['maintainer'] if 'maintainer' in self._args else None

    def get_repo(self) -> Optional[str]:
        return self._args['inrepo'] if 'inrepo' in self._args else None

    def is_advanced(self) -> bool:
        for fieldname in self._args.keys():
            if MetapackagesFilterInfo._fields[fieldname].advanced:
                return True
        return False


def get_packages_name_range(packages: Sequence[Package]) -> Tuple[Optional[str], Optional[str]]:
    firstname, lastname = None, None

    if packages:
        firstname = lastname = packages[0].effname
        for package in packages[1:]:
            lastname = max(lastname, package.effname)
            firstname = min(firstname, package.effname)

    return firstname, lastname


def packages_to_summary_items(packages: Iterable[Package], repo: Optional[str] = None, maintainer: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    # filter by either repo or maintainer, not both
    if repo is not None:
        maintainer = None

    sumtypes = ('explicit', 'newest', 'outdated', 'ignored')

    def summary_factory() -> Dict[str, Dict[str, Any]]:
        return {
            sumtype: defaultdict(set)
            for sumtype in sumtypes
        }

    summaries: Dict[str, Dict[str, Any]] = defaultdict(summary_factory)

    # pass 1: gather summaries in the intermediate format:
    # dict by metapackage name -> dict by summary type (e.g. table columns) -> hash by versioninfo of sets of families
    for package in packages:
        target = None

        versioninfo = UserVisibleVersionInfo(package)

        if (repo is not None and repo == package.repo) or (maintainer is not None and maintainer in package.maintainers):
            target = summaries[package.effname]['explicit']
        elif package.versionclass in [PackageStatus.OUTDATED, PackageStatus.LEGACY]:
            target = summaries[package.effname]['outdated']
            versioninfo.versionclass = PackageStatus.OUTDATED  # we don't need to differentiate legacy and outdated here
        elif package.versionclass in [PackageStatus.DEVEL, PackageStatus.NEWEST, PackageStatus.UNIQUE]:
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


def packages_to_metapackages(*packagesets: Iterable[Package]) -> Dict[str, List[Package]]:
    metapackages: Dict[str, List[Package]] = defaultdict(list)

    for packages in packagesets:
        for package in packages:
            metapackages[package.effname].append(package)

    return metapackages
