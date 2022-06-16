# Copyright (C) 2018-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Callable, cast

from repology.package import Package, PackageFlags
from repology.transformer.contexts import MatchContext, PackageContext
from repology.transformer.util import yaml_as_list


__all__ = ['get_action_generators']


# types
Action = Callable[[Package, PackageContext, MatchContext], None]
ActionGenerator = Callable[[Any], Action]


# machinery for action registration
_action_generators: list[tuple[str, ActionGenerator]] = []


def get_action_generators() -> list[tuple[str, ActionGenerator]]:
    return _action_generators


def _action_generator(func: ActionGenerator) -> ActionGenerator:
    _action_generators.append((func.__name__, func))
    return func


# actions
@_action_generator
def remove(ruledata: Any) -> Action:
    remove_flag = cast(bool, ruledata['remove'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.REMOVE, remove_flag)

    return action


@_action_generator
def ignore(ruledata: Any) -> Action:
    ignore_flag = cast(bool, ruledata['ignore'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.IGNORE, ignore_flag)

    return action


@_action_generator
def weak_devel(ruledata: Any) -> Action:
    weak_devel_flag = cast(bool, ruledata['weak_devel'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        # XXX: currently sets ignore; change to set non-viral variant of devel (#654)
        package.set_flag(PackageFlags.IGNORE, weak_devel_flag)

    return action


@_action_generator
def stable(ruledata: Any) -> Action:
    stable_flag = cast(bool, ruledata['stable'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.STABLE, stable_flag)

    return action


@_action_generator
def devel(ruledata: Any) -> Action:
    devel_flag = cast(bool, ruledata['devel'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.DEVEL, devel_flag)

    return action


@_action_generator
def p_is_patch(ruledata: Any) -> Action:
    p_is_patch_flag = cast(bool, ruledata['p_is_patch'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.P_IS_PATCH, p_is_patch_flag)

    return action


@_action_generator
def any_is_patch(ruledata: Any) -> Action:
    any_is_patch_flag = cast(bool, ruledata['any_is_patch'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.ANY_IS_PATCH, any_is_patch_flag)

    return action


@_action_generator
def sink(ruledata: Any) -> Action:
    sink_flag = cast(bool, ruledata['sink'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.SINK, sink_flag)

    return action


@_action_generator
def outdated(ruledata: Any) -> Action:
    outdated_flag = cast(bool, ruledata['outdated'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.OUTDATED, outdated_flag)

    return action


@_action_generator
def legacy(ruledata: Any) -> Action:
    legacy_flag = cast(bool, ruledata['legacy'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.LEGACY, legacy_flag)

    return action


@_action_generator
def nolegacy(ruledata: Any) -> Action:
    nolegacy_flag = cast(bool, ruledata['nolegacy'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.NOLEGACY, nolegacy_flag)

    return action


@_action_generator
def incorrect(ruledata: Any) -> Action:
    incorrect_flag = cast(bool, ruledata['incorrect'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.INCORRECT, incorrect_flag)

    return action


@_action_generator
def untrusted(ruledata: Any) -> Action:
    untrusted_flag = cast(bool, ruledata['untrusted'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.UNTRUSTED, untrusted_flag)

    return action


@_action_generator
def noscheme(ruledata: Any) -> Action:
    noscheme_flag = cast(bool, ruledata['noscheme'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.NOSCHEME, noscheme_flag)

    return action


@_action_generator
def rolling(ruledata: Any) -> Action:
    rolling_flag = cast(bool, ruledata['rolling'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.ROLLING, rolling_flag)

    return action


@_action_generator
def snapshot(ruledata: Any) -> Action:
    snapshot_flag = cast(bool, ruledata['snapshot'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        # XXX: the same as ignored for now
        package.set_flag(PackageFlags.IGNORE, snapshot_flag)

    return action


@_action_generator
def successor(ruledata: Any) -> Action:
    successor_flag = cast(bool, ruledata['successor'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        # XXX: the same as devel for now
        package.set_flag(PackageFlags.DEVEL, successor_flag)

    return action


@_action_generator
def debianism(ruledata: Any) -> Action:
    debianism_flag = cast(bool, ruledata['debianism'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        # XXX: the same as devel for now
        package.set_flag(PackageFlags.DEVEL, debianism_flag)

    return action


@_action_generator
def generated(ruledata: Any) -> Action:
    generated_flag = cast(bool, ruledata['generated'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        # XXX: the same as rolling for now
        package.set_flag(PackageFlags.ROLLING, generated_flag)

    return action


@_action_generator
def trace(ruledata: Any) -> Action:
    trace_flag = cast(bool, ruledata['trace'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.TRACE, trace_flag)

    return action


@_action_generator
def altver(ruledata: Any) -> Action:
    altver_flag = cast(bool, ruledata['altver'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.ALTVER, altver_flag)

    return action


@_action_generator
def altscheme(ruledata: Any) -> Action:
    altscheme_flag = cast(bool, ruledata['altscheme'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.ALTSCHEME, altscheme_flag)

    return action


@_action_generator
def vulnerable(ruledata: Any) -> Action:
    vulnerable_flag = cast(bool, ruledata['vulnerable'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.set_flag(PackageFlags.VULNERABLE, vulnerable_flag)

    return action


@_action_generator
def last(ruledata: Any) -> Action:
    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        match_context.last = True

    return action


@_action_generator
def addflavor(ruledata: Any) -> Action:
    tmp_flavors: list[str] | None

    if isinstance(ruledata['addflavor'], str):
        tmp_flavors = [ruledata['addflavor']]
    elif isinstance(ruledata['addflavor'], list):
        tmp_flavors = ruledata['addflavor']
    elif not isinstance(ruledata['addflavor'], bool):
        raise RuntimeError('addflavor must be boolean or str or list')
    else:
        tmp_flavors = None

    want_flavors: list[str] | None = tmp_flavors

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        flavors: list[str] = want_flavors if want_flavors else [package.effname]

        flavors = [match_context.sub_name_dollars(flavor, package.effname) for flavor in flavors]

        flavors = [flavor.strip('-') for flavor in flavors]

        package.flavors += [flavor for flavor in flavors if flavor]

    return action


@_action_generator
def setflavor(ruledata: Any) -> Action:
    tmp_flavors: list[str] | None

    if isinstance(ruledata['setflavor'], str):
        tmp_flavors = [ruledata['setflavor']]
    elif isinstance(ruledata['setflavor'], list):
        tmp_flavors = ruledata['setflavor']
    elif not isinstance(ruledata['setflavor'], bool):
        raise RuntimeError('setflavor must be boolean or str or list')
    else:
        tmp_flavors = None

    want_flavors: list[str] | None = tmp_flavors

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        flavors: list[str] = want_flavors if want_flavors else [package.effname]

        flavors = [match_context.sub_name_dollars(flavor, package.effname) for flavor in flavors]

        flavors = [flavor.strip('-') for flavor in flavors]

        package.flavors = [flavor for flavor in flavors if flavor]

    return action


@_action_generator
def resetflavors(ruledata: Any) -> Action:
    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.flavors = []

    return action


@_action_generator
def setbranch(ruledata: Any) -> Action:
    setbranch = cast(str, ruledata['setbranch'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.branch = match_context.sub_ver_dollars(setbranch, package.version)

    return action


@_action_generator
def setbranchcomps(ruledata: Any) -> Action:
    setbranchcomps = cast(int, ruledata['setbranchcomps'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.branch = '.'.join(re.split('[^a-zA-Z0-9]', package.version)[0:setbranchcomps])

    return action


@_action_generator
def addflag(ruledata: Any) -> Action:
    addflags = yaml_as_list(ruledata['addflag'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        for flag in addflags:
            package_context.add_flag(flag)

    return action


@_action_generator
def setname(ruledata: Any) -> Action:
    setname = cast(str, ruledata['setname'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.effname = match_context.sub_name_dollars(setname, package.effname)

    return action


@_action_generator
def setver(ruledata: Any) -> Action:
    setver = cast(str, ruledata['setver'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.version = match_context.sub_ver_dollars(setver, package.version)

    return action


@_action_generator
def setsubrepo(ruledata: Any) -> Action:
    setsubrepo = cast(str, ruledata['setsubrepo'])

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.subrepo = match_context.sub_name_dollars(setsubrepo, package.effname)

    return action


@_action_generator
def replaceinname(ruledata: Any) -> Action:
    replace_items = list(ruledata['replaceinname'].items())

    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        for pattern, replacement in replace_items:
            package.effname = package.effname.replace(pattern, replacement)

    return action


@_action_generator
def tolowername(ruledata: Any) -> Action:
    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package.effname = package.effname.lower()

    return action


@_action_generator
def warning(ruledata: Any) -> Action:
    def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        package_context.add_warning(ruledata['warning'])

    return action
