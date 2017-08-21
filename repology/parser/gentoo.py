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

import os
import xml.etree.ElementTree

from repology.package import Package
from repology.util import GetMaintainers
from repology.version import VersionCompare


def ParseConditionalExpr(string):
    words = string.split()
    result = []

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

        result.append(word)

        # rename
        if len(words) >= 2 and words[0] == '->':
            words = words[2:]

        # XXX: parse ( || foo bar ) construct used with licenses

    return result


def SanitizeVersion(version):
    origversion = version

    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class GentooGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

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

                metadata_path = os.path.join(package_path, 'metadata.xml')

                # parse maintainers from metadata.xml
                # these are the same for all ebuilds for current package
                maintainers = []
                if os.path.isfile(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as metafile:
                        meta = xml.etree.ElementTree.parse(metafile)

                        for entry in meta.findall('maintainer'):
                            email_node = entry.find('email')

                            if email_node is not None and email_node.text is not None:
                                maintainers += GetMaintainers(email_node.text)

                for ebuild in os.listdir(package_path):
                    if not ebuild.endswith('.ebuild'):
                        continue

                    pkg = Package()

                    pkg.name = package
                    pkg.category = category
                    pkg.maintainers = maintainers

                    pkg.version, pkg.origversion = SanitizeVersion(ebuild[len(package) + 1:-7])

                    if pkg.version.endswith('9999'):
                        # ignore versions for snapshots
                        pkg.ignoreversion = True

                    metadata_path = os.path.join(
                        path,
                        'metadata',
                        'md5-cache',
                        category,
                        package + '-' + (pkg.origversion if pkg.origversion else pkg.version)
                    )
                    if os.path.isfile(metadata_path):
                        with open(metadata_path, 'r', encoding='utf-8') as metadata_file:
                            for line in metadata_file:
                                line = line.strip()
                                key, value = line.split('=', 1)

                                if key == 'DESCRIPTION':
                                    pkg.comment = value
                                elif key == 'HOMEPAGE':
                                    pkg.homepage = value.split(' ')[0]  # XXX: save all urls
                                elif key == 'LICENSE':
                                    if value.find('(') != -1:
                                        # XXX: conditionals and OR's: need more
                                        # complex parsing and backend support
                                        pkg.licenses.append(value)
                                    else:
                                        pkg.licenses += value.split(' ')
                                elif key == 'SRC_URI':
                                    pkg.downloads += ParseConditionalExpr(value)

                    result.append(pkg)

        return result
