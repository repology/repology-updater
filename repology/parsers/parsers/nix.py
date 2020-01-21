# Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Dict, Iterable, List, Union

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_dict
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


def extract_nix_maintainers(items: Iterable[Union[str, Dict[str, str]]]) -> Iterable[str]:
    for item in items:
        # old format, currently used in stable; parse email out of 'name <email>' string
        # items without closing '>' are quite common, just skip them
        if isinstance(item, str):
            for maintainer in extract_maintainers(item):
                if '<' not in maintainer:
                    yield maintainer
        elif isinstance(item, dict):
            if 'email' in item:
                yield item['email'].lower()
            # do we need these?
            #if 'github' in item:
            #    yield item['github'].lower() + '@github'


def extract_nix_licenses(whatever: Any) -> List[str]:
    if isinstance(whatever, str):
        return [whatever]
    elif isinstance(whatever, list):
        return sum(map(extract_nix_licenses, whatever), [])
    elif isinstance(whatever, dict) and 'spdxId' in whatever:
        return [whatever['spdxId']]
    elif isinstance(whatever, dict) and 'fullName' in whatever:
        return [whatever['fullName']]
    elif isinstance(whatever, dict) and 'fullname' in whatever:
        return [whatever['fullname']]
    else:
        #factory.log('unable to parse license {}'.format(whatever), severity=Logger.ERROR)
        return []


_BLACKLIST1 = {
    'liblqr': ['1'],
    'python2.7': ['3to2'],
    'python3.6': ['3to2'],
    'python3.7': ['3to2'],
    'python3.8': ['3to2'],
    'libretro': ['4do'],
    'polkit-qt': ['1-qt4', '1-qt5'],
    'Dell': ['5130cdn-Color-Laser'],
    'epson': ['201106w'],
    'MPH': ['2B-Damase'],
    'x86': ['64bit'],
    'fuse': ['7z-ng'],
}

_BLACKLIST2 = {
    'airstrike-pre',
}


class NixJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for key, packagedata in iter_json_dict(path, ('packages', None), encoding='utf-8'):
            with factory.begin(key) as pkg:
                # these should eventually go away as soon as the data is fixed
                # in nix (e.g. via manual pnames) and is properly exposed
                if 'node-_at' in packagedata['name']:
                    pkg.log('dropping, garbage name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue

                if '--' in packagedata['name']:
                    pkg.log('dropping, garbage name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue

                if packagedata['name'].startswith('luajit-2.1.0-beta3-'):
                    pkg.log('dropping, garbage name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue

                if packagedata['name'].startswith('palp-6d'):
                    pkg.log('dropping, garbage name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue

                if re.match('cudatoolkit-[0-9.-]+-cudnn', packagedata['name']):
                    pkg.log('dropping, garbage name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue

                if re.match('nccl-[0-9.-]+-cuda', packagedata['name']):
                    pkg.log('dropping, garbage name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue

                skip = False
                if packagedata['pname'] in _BLACKLIST1:
                    for verprefix in _BLACKLIST1[packagedata['pname']]:
                        if packagedata['version'].startswith(verprefix):
                            pkg.log('dropping {}, "{}" does not belong to version'.format(packagedata['name'], verprefix), severity=Logger.ERROR)
                            skip = True
                            break

                if packagedata['pname'] in _BLACKLIST2:
                    pkg.log('dropping {}, "{}" does not belong to name'.format(packagedata['name'], packagedata['pname'].rsplit('-')[-1]), severity=Logger.ERROR)
                    skip = True

                for verprefix in ['100dpi', '75dpi']:
                    if packagedata['version'].startswith(verprefix):
                        pkg.log('dropping "{}", "{}" does not belong to version'.format(packagedata['name'], verprefix), severity=Logger.ERROR)
                        skip = True
                        break

                if skip:
                    continue

                if not packagedata['version']:
                    continue  # no version - silently ignore

                if re.match('[0-9].*[a-z].*-[0-9]', packagedata['version'].lower()):
                    letters = ''.join(c for c in packagedata['version'].lower() if c.isalpha())
                    if letters not in ['alpha', 'beta', 'rc', 'a', 'b', 'pre', 'post', 'rev', 'q', 'u', 'build', 'unstable']:
                        pkg.log('"{}": suspicious version "{}", worth rechecking'.format(packagedata['name'], packagedata['version']), severity=Logger.WARNING)

                pname = packagedata['pname']
                version = packagedata['version']

                # This is temporary solution (see #854) which overrides pname and version with ones
                # (ambigiously) parsed from name. That's what nix currently does (instead of exposing
                # explicitly set pname and version), and we do the same instead of using pname/version
                # provided by them to avoid unexpected change in data when/if they change their logic
                # As soon as they do and changed data is verified, this block may be removed
                match = re.match('(.+?)-([0-9].*)$', packagedata['name'])
                if match is None:
                    pkg.log('cannot parse name "{}"'.format(packagedata['name']), severity=Logger.ERROR)
                    continue
                else:
                    pname = match.group(1)
                    version = match.group(2)

                pkg.add_name(key, NameType.NIX_ATTRIBUTE_PATH)
                pkg.add_name(pname, NameType.NIX_PNAME)
                pkg.set_version(version)

                meta = packagedata['meta']

                keyparts = key.split('.')
                if len(keyparts) > 1:
                    pkg.add_categories(keyparts[0])

                # XXX: mode to rules
                if pname.endswith('-git'):
                    pkg.add_name(pname[:-4], NameType.NIX_PNAME)
                    pkg.set_flags(PackageFlags.IGNORE)

                # XXX: mode to rules
                if re.match('.*20[0-9]{2}-[0-9]{2}-[0-9]{2}', pkg.version):
                    pkg.set_flags(PackageFlags.IGNORE)

                # XXX: mode to rules
                if re.match('[0-9a-f]*[a-f][0-9a-f]*$', pkg.version) and len(pkg.version) >= 7:
                    pkg.set_flags(PackageFlags.IGNORE)

                pkg.add_homepages(meta.get('homepage'))

                if 'description' in meta:
                    pkg.set_summary(meta['description'].replace('\n', ' '))

                if 'maintainers' in meta:
                    if not isinstance(meta['maintainers'], list):
                        pkg.log('maintainers "{}" is not a list'.format(meta['maintainers']), severity=Logger.ERROR)
                    else:
                        pkg.add_maintainers(extract_nix_maintainers(meta['maintainers']))

                if 'license' in meta:
                    pkg.add_licenses(extract_nix_licenses(meta['license']))

                if 'position' in meta:
                    posfile, posline = meta['position'].rsplit(':', 1)
                    pkg.set_extra_field('posfile', posfile)
                    pkg.set_extra_field('posline', posline)

                    if posfile.startswith('pkgs/development/haskell-modules'):
                        pkg.set_flags(PackageFlags.ROLLING)  # XXX: haskell modules are autogenerated in nix: https://github.com/NixOS/nixpkgs/commits/master/pkgs/development/haskell-modules/hackage-packages.nix

                yield pkg
