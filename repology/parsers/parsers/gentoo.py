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

import os
import xml.etree.ElementTree

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple
from repology.parsers.cpe import cpe_parse
from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


def _parse_conditional_expr(string: str) -> Iterable[str]:
    words = string.split()

    nestlevel = 0
    while words:
        word = words.pop(0)

        # enter condition
        if '/' not in word and word.endswith('?') and words and words[0] == '(':
            words.pop(0)
            nestlevel += 1
            continue

        # leave condition
        if word == ')':
            nestlevel -= 1
            continue

        yield word

        # rename
        if len(words) >= 2 and words[0] == '->':
            words = words[2:]

        # XXX: parse ( || foo bar ) construct used with licenses


def _iter_packages(path: str) -> Iterable[Tuple[str, str]]:
    for category in os.listdir(path):
        category_path = os.path.join(path, category)
        if not os.path.isdir(category_path) or category.startswith('.') or category in ['acct-group', 'acct-user', 'metadata', 'virtual']:
            continue

        for package in os.listdir(category_path):
            package_path = os.path.join(category_path, package)
            if not os.path.isdir(package_path):
                continue

            yield (category, package)


def _iter_ebuilds(path: str, category: str, package: str) -> Iterable[str]:
    for ebuild in os.listdir(os.path.join(path, category, package)):
        if not ebuild.endswith('.ebuild'):
            continue

        yield ebuild[:-7]  # strip extension


_link_templates_by_upstream_type = {
    'bitbucket': 'https://bitbucket.org/{}',
    'cpan': 'https://metacpan.org/release/{}',
    'cpan-module': None,  # should be handled by cpan
    'ctan': 'https://www.ctan.org/pkg/{}',
    'freecode': 'http://freecode.com/projects/{}',
    'freshmeat': 'http://freshmeat.net/projects/{}/',
    'github': 'https://github.com/{}',
    'gitlab': 'https://gitlab.com/{}',
    'google-code': 'https://code.google.com/p/{}/',
    'launchpad': 'https://launchpad.net/{}',
    'pear': 'http://pear.php.net/package/{}',
    'pypi': 'https://pypi.org/project/{}/',
    'rubygems': 'https://rubygems.org/gems/{}',
    'sourceforge': 'https://sourceforge.net/projects/{}/',
    'sourceforge-jp': 'https://osdn.net/projects/{}/',
}


@dataclass
class _ParsedXmlMetadata:
    maintainers: List[str] = field(default_factory=list)
    upstreams: List[str] = field(default_factory=list)
    unsupported_upstream_types: Set[str] = field(default_factory=set)
    cpe: Optional[str] = None

    def handle_upstream(self, type_: str, value: str) -> None:
        if type_ == 'cpe':
            self.cpe = value
        elif type_ in _link_templates_by_upstream_type:
            link_template = _link_templates_by_upstream_type[type_]

            if link_template is not None:
                self.upstreams.append(link_template.format(value.strip()))
        else:
            self.unsupported_upstream_types.add(type_)


def _parse_xml_metadata(path: str) -> _ParsedXmlMetadata:
    with open(path, 'r', encoding='utf-8') as metafile:
        meta = xml.etree.ElementTree.parse(metafile)

    output = _ParsedXmlMetadata()

    for entry in meta.findall('maintainer'):
        email_node = entry.find('email')

        if email_node is not None and email_node.text is not None:
            output.maintainers += extract_maintainers(email_node.text)

    for entry in meta.findall('upstream'):
        for remote_id_node in entry.findall('remote-id'):
            if remote_id_node.text:
                output.handle_upstream(remote_id_node.attrib['type'], remote_id_node.text.strip())

    return output


def _parse_md5cache_metadata(path: str) -> Dict[str, str]:
    result: Dict[str, str] = {}

    with open(path, 'r', encoding='utf-8') as metadata_file:
        for line in metadata_file:
            line = line.strip()
            key, value = line.split('=', 1)

            result[key] = value

    return result


class GentooGitParser(Parser):
    _require_xml_metadata: bool
    _require_md5cache_metadata: bool

    def __init__(self, require_md5cache_metadata: bool = True, require_xml_metadata: bool = False) -> None:
        self._require_xml_metadata = require_xml_metadata
        self._require_md5cache_metadata = require_md5cache_metadata

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('-')

        for category, package in _iter_packages(path):
            with factory.begin(category + '/' + package) as pkg:
                pkg.add_name(package, NameType.GENTOO_NAME)
                pkg.add_name(category + '/' + package, NameType.GENTOO_FULL_NAME)
                pkg.add_categories(category)

                xml_metadata_path = os.path.join(path, category, package, 'metadata.xml')
                if os.path.isfile(xml_metadata_path):
                    xml_metadata = _parse_xml_metadata(xml_metadata_path)
                    for upstream_type in xml_metadata.unsupported_upstream_types:
                        pkg.log(f'Unsupported upstream type {upstream_type}', Logger.ERROR)
                elif self._require_xml_metadata:
                    pkg.log('cannot find metadata ({}), package dropped'.format(os.path.relpath(xml_metadata_path, path)), Logger.ERROR)
                    continue
                else:
                    xml_metadata = _ParsedXmlMetadata()

                pkg.add_maintainers(xml_metadata.maintainers)

                if xml_metadata.cpe is not None:
                    cpe = cpe_parse(xml_metadata.cpe)
                    pkg.add_cpe(cpe.part, cpe.vendor)

                for ebuild in _iter_ebuilds(path, category, package):
                    subpkg = pkg.clone(append_ident='/' + ebuild)

                    subpkg.set_version(ebuild[len(package) + 1:], normalize_version)
                    if subpkg.version.endswith('9999'):
                        subpkg.set_flags(PackageFlags.ROLLING)

                    md5cache_metadata_path = os.path.join(path, 'metadata', 'md5-cache', category, ebuild)

                    if os.path.isfile(md5cache_metadata_path):
                        md5cache_metadata = _parse_md5cache_metadata(md5cache_metadata_path)

                        subpkg.set_summary(md5cache_metadata.get('DESCRIPTION'))

                        if 'LICENSE' in md5cache_metadata:
                            if '(' in md5cache_metadata['LICENSE']:
                                # XXX: conditionals and OR's: need more
                                # complex parsing and backend support
                                subpkg.add_licenses(md5cache_metadata['LICENSE'])
                            else:
                                subpkg.add_licenses(md5cache_metadata['LICENSE'].split(' '))

                        if 'SRC_URI' in md5cache_metadata:
                            # skip local files
                            subpkg.add_downloads(filter(lambda s: '/' in s, _parse_conditional_expr(md5cache_metadata['SRC_URI'])))

                        subpkg.add_homepages(md5cache_metadata.get('HOMEPAGE', '').split(' '))
                    elif self._require_md5cache_metadata:
                        subpkg.log('cannot find metadata ({}), package dropped'.format(os.path.relpath(md5cache_metadata_path, path)), Logger.ERROR)
                        continue

                    # upstreams should be added after "real" homepages
                    subpkg.add_homepages(xml_metadata.upstreams)

                    yield subpkg
