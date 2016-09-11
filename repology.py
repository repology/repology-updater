#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import subprocess
import csv

def SplitPackageNameVersion(pkgname):
    hyphen_pos = pkgname.rindex('-')

    name = pkgname[0 : hyphen_pos]
    version = pkgname[hyphen_pos + 1 : ]

    return name, version

def SanitizeFreeBSDVersion(version):
    pos = version.rfind(',')
    if pos != -1:
        version = version[0:pos]

    pos = version.rfind('_')
    if pos != -1:
        version = version[0:pos]

    return version

def SanitizeDebianVersion(version):
    pos = version.rfind('-')
    if pos != -1:
        version = version[0:pos]

    return version

def ParseFreeBSD(path):
    result = []

    with open(path) as file:
        reader = csv.reader(file, delimiter='|')
        for row in reader:
            name, version = SplitPackageNameVersion(row[0])
            version = SanitizeFreeBSDVersion(version)
            comment = row[3]
            maintainer = row[5]
            category = row[6].split(' ')[0]

            result.append({
                'name': name,
                'version': version,
                'category': category,
                'comment': comment,
                'maintainer' :maintainer
            })

    return result

def ParseDebian(path):
    result = []

    with open(path) as file:
        data = {}
        for line in file:
            if line == "\n":
                result.append(data)
                data = {}
            elif line.startswith('Package: '):
                data['name'] = line[9:-1]
            elif line.startswith('Version: '):
                data['version'] = SanitizeDebianVersion(line[9:-1])
            elif line.startswith('Maintainer: '):
                data['maintainer'] = line[12:-1]
            elif line.startswith('Section: '):
                data['category'] = line[9:-1]
            elif line.startswith('Homepage: '):
                data['homepage'] = line[10:-1]

    return result

def Main():
    if not os.path.isfile('freebsd.list'):
        subprocess.check_call("wget -qO- http://www.FreeBSD.org/ports/INDEX-11.bz2 | bunzip2 > freebsd.list", shell = True)
    if not os.path.isfile('debian.list'):
        subprocess.check_call("wget -qO- http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz | gunzip > debian.list", shell = True)

    print(ParseFreeBSD('freebsd.list'))
    print(ParseDebian('debian.list'))

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
