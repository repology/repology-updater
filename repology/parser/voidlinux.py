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
import re
import sys

from repology.package import Package
from repology.version import VersionCompare


def expandDownloadUrlTemplates(url, pkgname=None, version=None, homepage=None):
    url_aliases = {
            'CPAN_SITE': 'http://cpan.perl.org/modules/by-module',
            'DEBIAN_SITE': 'http://ftp.debian.org/debian/pool',
            'FREEDESKTOP_SITE': 'http://freedesktop.org/software',
            'GNOME_SITE': 'http://ftp.gnome.org/pub/GNOME/sources',
            'GNU_SITE': 'http://mirrors.kernel.org/gnu',
            'KERNEL_SITE': 'http://www.kernel.org/pub/linux',
            'MOZILLA_SITE': 'http://ftp.mozilla.org/pub',
            'NONGNU_SITE': 'http://download.savannah.nongnu.org/releases',
            'PYPI_SITE': 'https://files.pythonhosted.org/packages/source',
            'SOURCEFORGE_SITE': 'http://downloads.sourceforge.net/sourceforge',
            'UBUNTU_SITE': 'http://archive.ubuntu.com/ubuntu/pool',
            'XORG_HOME': 'http://xorg.freedesktop.org/wiki/',
            'XORG_SITE': 'http://xorg.freedesktop.org/releases/individual',
            }

    if pkgname:
        url_aliases['pkgname'] = pkgname
    if version:
        url_aliases['version'] = version
    if homepage:
        url_aliases['homepage'] = homepage

    for alias, replacement in url_aliases.items():
        url = url \
                .replace('$' + alias, replacement) \
                .replace('${' + alias + '}', replacement)

    return url


class VoidLinuxGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        source_path = os.path.join(path, 'srcpkgs')
        for package_name in os.listdir(source_path):
            package_path = os.path.join(source_path, package_name)
            template_path = os.path.join(package_path, 'template')

            pkg = Package()

            if os.path.isfile(template_path):
                with open(template_path, 'r', encoding='utf-8', errors='ignore') as template:
                    for line in template:
                        line = line.strip()
                        if line.startswith('pkgname='):
                            pkg.name = line[8:].strip(' "')
                        if line.startswith('version='):
                            pkg.version = line[8:].strip(' "')
                        if line.startswith('license='):
                            pkg.licenses += [x.strip() for x in line[8:].strip('"').split(",")]
                        if line.startswith('short_desc='):
                            pkg.comment = line[11:].strip(' "')
                        if line.startswith('homepage='):
                            pkg.homepage = line[9:].strip(' "')

                        if line.startswith('distfiles='):
                            distfiles = line[10:].strip(' "')

                            distfiles = expandDownloadUrlTemplates(distfiles, pkgname=pkg.name, version=pkg.version, homepage=pkg.homepage)

                            for distfile in distfiles.split():
                                # Template format allows specifying target file with a ">",
                                # e.g. http://foo.org/bar-1.0.tar.gz>bar.tar.gz
                                distfile = distfile.split('>')[0]

                                if distfile.find('$') == -1:
                                    pkg.downloads.append(distfile)

                                else:
                                    print('WARNING: Skipping download URL for {} {} because it contains an unknown variable.'.format(pkg.name, pkg.version), file=sys.stderr)

            result.append(pkg)

        return result
