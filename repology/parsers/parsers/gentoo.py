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
from typing import Iterable

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


def _parse_conditional_expr(string):
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


def _iter_packages(path):
    for category in os.listdir(path):
        category_path = os.path.join(path, category)
        if not os.path.isdir(category_path):
            continue
        if category == 'virtual' or category == 'metadata':
            continue

        for package in os.listdir(category_path):
            package_path = os.path.join(category_path, package)
            if not os.path.isdir(package_path):
                continue

            yield (category, package)


def _iter_ebuilds(path, category, package):
    for ebuild in os.listdir(os.path.join(path, category, package)):
        if not ebuild.endswith('.ebuild'):
            continue

        yield ebuild[:-7]  # strip extension


def _construct_upstream_link(upstream_type, arg, pkg):
    if   upstream_type == 'bitbucket':      return 'https://bitbucket.org/{}'.format(arg)  # noqa
    elif upstream_type == 'cpan':           return 'https://metacpan.org/release/{}'.format(arg)  # noqa
    elif upstream_type == 'cpan-module':    return None  # should be handled by cpan  # noqa
    elif upstream_type == 'cpe':            return None  # ignore  # noqa
    elif upstream_type == 'ctan':           return 'https://www.ctan.org/pkg/{}'.format(arg)  # noqa
    elif upstream_type == 'freecode':       return 'http://freecode.com/projects/{}'.format(arg)  # noqa
    elif upstream_type == 'freshmeat':      return 'http://freshmeat.net/projects/{}/'.format(arg)  # noqa
    elif upstream_type == 'github':         return 'https://github.com/{}'.format(arg)  # noqa
    elif upstream_type == 'gitlab':         return 'https://gitlab.com/{}'.format(arg)  # noqa
    elif upstream_type == 'google-code':    return 'https://code.google.com/p/{}/'.format(arg)  # noqa
    elif upstream_type == 'launchpad':      return 'https://launchpad.net/{}'.format(arg)  # noqa
    elif upstream_type == 'pear':           return 'http://pear.php.net/package/{}'.format(arg)  # noqa
    elif upstream_type == 'pypi':           return 'https://pypi.org/project/{}/'.format(arg)  # noqa
    elif upstream_type == 'rubygems':       return 'https://rubygems.org/gems/{}'.format(arg)  # noqa
    elif upstream_type == 'sourceforge':    return 'https://sourceforge.net/projects/{}/'.format(arg)  # noqa
    elif upstream_type == 'sourceforge-jp': return 'https://osdn.net/projects/{}/'.format(arg)  # noqa

    pkg.log('Unsupported upstream type {}'.format(upstream_type), Logger.ERROR)
    return None


def _parse_package_metadata_xml(path, category, package, pkg):
    metadata_path = os.path.join(path, category, package, 'metadata.xml')

    maintainers = []
    upstreams = []

    if not os.path.isfile(metadata_path):
        return (maintainers, upstreams)

    with open(metadata_path, 'r', encoding='utf-8') as metafile:
        meta = xml.etree.ElementTree.parse(metafile)

    for entry in meta.findall('maintainer'):
        email_node = entry.find('email')

        if email_node is not None and email_node.text is not None:
            maintainers += extract_maintainers(email_node.text)

    for entry in meta.findall('upstream'):
        for remote_id_node in entry.findall('remote-id'):
            upstreams.append(_construct_upstream_link(remote_id_node.attrib['type'], remote_id_node.text.strip(), pkg))

    return (maintainers, upstreams)


def _parse_md5cache_metadata_xml(path, category, ebuild):
    metadata_path = os.path.join(path, 'metadata', 'md5-cache', category, ebuild)

    result = {}

    if not os.path.isfile(metadata_path):
        return result

    with open(metadata_path, 'r', encoding='utf-8') as metadata_file:
        for line in metadata_file:
            line = line.strip()
            key, value = line.split('=', 1)

            result[key] = value

    return result


class GentooGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('-')

        for category, package in _iter_packages(path):
            pkg = factory.begin(category + '/' + package)

            pkg.set_name(package)
            pkg.add_categories(category)

            maintainers, upstreams = _parse_package_metadata_xml(path, category, package, pkg)

            pkg.add_maintainers(maintainers)

            for ebuild in _iter_ebuilds(path, category, package):
                subpkg = pkg.clone(append_ident='/' + ebuild)

                subpkg.set_version(ebuild[len(package) + 1:], normalize_version)
                if subpkg.version.endswith('9999'):
                    subpkg.set_flags(PackageFlags.rolling)

                metadata = _parse_md5cache_metadata_xml(path, category, ebuild)

                subpkg.set_summary(metadata.get('DESCRIPTION'))

                if 'LICENSE' in metadata:
                    if '(' in metadata['LICENSE']:
                        # XXX: conditionals and OR's: need more
                        # complex parsing and backend support
                        subpkg.add_licenses(metadata['LICENSE'])
                    else:
                        subpkg.add_licenses(metadata['LICENSE'].split(' '))

                if 'SRC_URI' in metadata:
                    # skip local files
                    subpkg.add_downloads(filter(lambda s: '/' in s, _parse_conditional_expr(metadata['SRC_URI'])))

                homepages = metadata.get('HOMEPAGE', '').split(' ')
                subpkg.add_homepages(homepages)

                homepages = set(homepages)

                for upstream in upstreams:
                    if upstream and upstream not in homepages:
                        subpkg.add_homepages(upstream)

                yield subpkg
