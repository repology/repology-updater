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
import sys
import subprocess
import csv
from pkg_resources import parse_version

class RepositoryProcessor:
    src = None
    path = None

    def __init__(self, path, src):
        self.path = path
        self.src = src

    def IsUpToDate(self):
        return True

    def Download(self):
        pass

    def Parse(self):
        return []

class FreeBSDIndexProcessor(RepositoryProcessor):
    def IsUpToDate(self):
        return os.path.isfile(self.path)

    def Download(self):
        subprocess.check_call("wget -qO- %s | bunzip2 > %s" % (self.src, self.path), shell = True)

    @staticmethod
    def SplitPackageNameVersion(pkgname):
        hyphen_pos = pkgname.rindex('-')

        name = pkgname[0 : hyphen_pos]
        version = pkgname[hyphen_pos + 1 : ]

        return name, version

    @staticmethod
    def SanitizeVersion(version):
        pos = version.rfind(',')
        if pos != -1:
            version = version[0:pos]

        pos = version.rfind('_')
        if pos != -1:
            version = version[0:pos]

        return version

    def Parse(self):
        result = []

        with open(self.path) as file:
            reader = csv.reader(file, delimiter='|')
            for row in reader:
                name, version = self.SplitPackageNameVersion(row[0])
                version = self.SanitizeVersion(version)
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

class DebianSourcesProcessor(RepositoryProcessor):
    def IsUpToDate(self):
        return os.path.isfile(self.path)

    def Download(self):
        subprocess.check_call("wget -qO- %s | gunzip > %s" % (self.src, self.path), shell = True)

    @staticmethod
    def SanitizeVersion(version):
        pos = version.rfind('-')
        if pos != -1:
            version = version[0:pos]

        pos = version.find(':')
        if pos != -1:
            version = version[pos+1:]

        return version

    def Parse(self):
        result = []

        with open(self.path) as file:
            data = {}
            for line in file:
                if line == "\n":
                    result.append(data)
                    data = {}
                elif line.startswith('Package: '):
                    data['name'] = line[9:-1]
                elif line.startswith('Version: '):
                    data['version'] = self.SanitizeVersion(line[9:-1])
                elif line.startswith('Maintainer: '):
                    data['maintainer'] = line[12:-1]
                elif line.startswith('Section: '):
                    data['category'] = line[9:-1]
                elif line.startswith('Homepage: '):
                    data['homepage'] = line[10:-1]

        return result

REPOSITORIES = [
    { 'name': "FreeBSD Ports", 'processor': FreeBSDIndexProcessor("freebsd.list", "http://www.FreeBSD.org/ports/INDEX-11.bz2") },
    { 'name': 'Debian Stable', 'processor': DebianSourcesProcessor("debian.list", "http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz") },
]

def MixRepositories(repositories):
    packages = {}

    for repository in repositories:
        for package in repository['processor'].Parse():
            pkgname = package['name']
            if not pkgname in packages:
                packages[pkgname] = {}
            packages[pkgname][repository['name']] = package

    return packages

def PrintPackageTable(packages, repositories):
    print("<html>")
    print("<head>");
    print("<html><head><title>Repology</title>")
    print("<link rel=\"stylesheet\" media=\"screen\" href=\"repology.css\">")
    print("</head>")
    print("<body>")
    print("<table>")
    print("<tr><th>Package</th>")
    for repository in repositories:
        print("<th>%s</th>" % repository['name'])
    print("</tr>")
    for pkgname in sorted(packages.keys()):
        package = packages[pkgname]
        print("<tr>")
        print("<td>%s</td>" % (pkgname))

        bestversion = None
        for subpackage in package.values():
            if 'version' in subpackage:
                if bestversion is None:
                    bestversion = subpackage['version']
                else:
                    if bestversion is None or parse_version(subpackage['version']) > parse_version(bestversion):
                        bestversion = subpackage['version']

        for repository in repositories:
            if repository['name'] in package:
                version = package[repository['name']]['version']
                if version == bestversion:
                    print("<td><span class=\"version good\">%s</span></td>" % version)
                else:
                    print("<td><span class=\"version bad\">%s</span></td>" % version)
            else:
                print("<td>-</td>")
        print("</tr>")
    print("</table>")
    print("</body>")
    print("</html>")

def Main():
    for repository in REPOSITORIES:
        print("===> Downloading for %s" % repository['name'], file=sys.stderr)
        if repository['processor'].IsUpToDate():
            print("Up to date", file=sys.stderr)
        else:
            repository['processor'].Download()

    print("===> Processing", file=sys.stderr)
    PrintPackageTable(MixRepositories(REPOSITORIES), REPOSITORIES)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
