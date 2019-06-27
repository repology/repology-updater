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
from typing import Any, Dict, Iterable, List, Union

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


_DEBIAN_VERSION_BAD_SUFFIX_RE = re.compile('[.~+-]?(dfsg|ubuntu|mx).*', re.IGNORECASE)
_DEBIAN_VERSION_GOOD_SUFFIX_RE = re.compile('((?:a|b|r|alpha|beta|rc|rcgit|pre|patch|git|svn|cvs|hg|bzr|darcs|dev)[.-]?[0-9]+(?:\\.[0-9]+)*|(?:alpha|beta|rc))', re.IGNORECASE)
_DEBIAN_VERSION_SUFFIX_SEP_RE = re.compile('[~+-]')
_DEBIAN_KEYVAL_RE = re.compile('([A-Za-z0-9_-]+):(.*?)')


def normalize_version(version: str) -> str:
    # epoch
    pos = version.find(':')
    if pos != -1:
        version = version[pos + 1:]

    # revision
    pos = version.rfind('-')
    if pos != -1:
        version = version[0:pos]

    # garbage debian/ubuntu addendums
    version = _DEBIAN_VERSION_BAD_SUFFIX_RE.sub('', version)

    # remove suffixes
    version, *suffixes = _DEBIAN_VERSION_SUFFIX_SEP_RE.split(version)

    # append useful suffixes
    good_suffixes = []
    for suffix in suffixes:
        match = _DEBIAN_VERSION_GOOD_SUFFIX_RE.match(suffix)
        if match:
            good_suffixes.append(match.group(1))

    version += '.'.join(good_suffixes)

    return version


class DebianSourcesParser(Parser):
    def __init__(self, project_name_from_source: bool = False) -> None:
        self.project_name_from_source = project_name_from_source

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path, encoding='utf-8', errors='ignore') as file:
            current_data: Dict[str, Union[str, List[str]]] = {}
            last_key = None

            for line in file:
                line = line.rstrip('\n')

                # empty line, dump package
                if line == '':
                    if not current_data:
                        continue  # may happen on empty package list

                    pkg = factory.begin()

                    def get_field(key: str, type_: Any = str, default: Any = None) -> Any:
                        if key in current_data:
                            if type_ is None or isinstance(current_data[key], type_):
                                return current_data[key]
                            else:
                                pkg.log('unable to parse field {}'.format(key), severity=Logger.ERROR)
                                return default
                        else:
                            return default

                    pkg.set_name(get_field('Package'))
                    pkg.set_version(get_field('Version'), normalize_version)
                    pkg.add_maintainers(extract_maintainers(get_field('Maintainer')))
                    pkg.add_maintainers(extract_maintainers(get_field('Uploaders')))
                    pkg.add_categories(get_field('Section'))
                    pkg.add_homepages(get_field('Homepage'))

                    # This is long description
                    #pkg.comment = get_field('Description', type_=None)
                    #if isinstance(pkg.comment, list):
                    #    pkg.set_summary(' '.join(pkg.comment))

                    source = get_field('Source')
                    if source:
                        pkg.set_extra_field('source', source)

                        # XXX: this is only used in OpenWRT ATM
                        # We assume that Source field is a package name or something path-like
                        if self.project_name_from_source:
                            srcname = source.split('/')[-1]
                            pkg.set_basename(srcname)
                            pkg.set_extra_field('srcname', srcname)

                    yield pkg

                    current_data = {}
                    last_key = None
                    continue

                # key - value pair
                match = _DEBIAN_KEYVAL_RE.fullmatch(line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    current_data[key] = value
                    last_key = key
                    continue

                # continuation of previous key
                if line.startswith(' '):
                    if last_key is None:
                        raise RuntimeError('unable to parse line: {}'.format(line))

                    value = line.strip()
                    if not isinstance(current_data[last_key], list):
                        current_data[last_key] = [current_data[last_key]]  # type: ignore
                    current_data[last_key].append(value)  # type: ignore
                    continue

                raise RuntimeError('unable to parse line: {}'.format(line))
