# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
from typing import Dict, Iterable, Optional

import lxml

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


def _parse_info_file(filename: str) -> Dict[str, str]:
    with open(filename, 'r') as infofile:
        return _parse_info(infofile.read())


def _parse_info(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    current_multiline_key: Optional[str] = None
    multiline_depth = 0

    for line in text.split('\n'):
        line = line.split('#', 1)[0].strip()

        if not line:
            continue

        if multiline_depth:
            if line == '<<':
                multiline_depth -= 1
            elif line.endswith('<<'):
                multiline_depth += 1

            if multiline_depth and current_multiline_key:
                result[current_multiline_key] += line + '\n'
        else:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()

            if val == '<<':
                current_multiline_key = key.lower()
                multiline_depth = 1
                result[key.lower()] = ''
            else:
                result[key.lower()] = val

    return result


class FinkGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for filename in walk_tree(path, suffix='.info'):
            rel_filename = os.path.relpath(filename, path)

            with factory.begin(rel_filename) as pkg:
                info = _parse_info_file(filename)

                for nestedkey in ['info4', 'info3', 'info2']:
                    if nestedkey in info:
                        info.update(_parse_info(info[nestedkey]))

                pkg.set_name(info['package'])
                pkg.set_version(info['version'])

                if '%' in info['package']:
                    # XXX: not usable because of too complex parsing is required for substitutions like
                    # package-stash-pm%type-pkg[perl]
                    pkg.log('unsupported substitution in package name: {}'.format(info['package']), severity=Logger.ERROR)
                    continue

                for key in ['homepage', 'source']:
                    if key in info:
                        # https://github.com/fink/fink/blob/848234952865c097f1a9c5b9cc4aa616546d906b/perlmod/Fink/PkgVersion.pm#L656-L671
                        replacements = {
                            '%v': info['version'],
                            '%n': info['package'],
                            '%m': info.get('architecture') or 'x86_64',  # can we use fixed arch to generate a download url?
                        }

                        for replkey, replacement in replacements.items():
                            info[key] = info[key].replace(replkey, replacement)

                        if '%' in info[key]:
                            pkg.log('probably unsupported substitution in {}: {}'.format(key, info[key]), severity=Logger.ERROR)

                pkg.add_downloads(info.get('source'))
                pkg.add_homepages(info.get('homepage'))

                pkg.add_licenses(info.get('license'))
                pkg.add_maintainers(extract_maintainers(info['maintainer']))

                pkg.set_extra_field('infopath', rel_filename)

                yield pkg


class FinkPdbParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('-')

        for row in lxml.html.parse(path).getroot().xpath('.//table[@class="pdb"]')[0].xpath('./tr[@class="package"]'):
            with factory.begin() as pkg:
                pkg.set_name(row.xpath('./td[1]/a')[0].text)
                pkg.set_version(row.xpath('./td[2]')[0].text, normalize_version)
                pkg.set_summary(row.xpath('./td[3]')[0].text)

                yield pkg
