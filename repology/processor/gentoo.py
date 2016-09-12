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
from pkg_resources import parse_version

from .common import RepositoryProcessor

class GentooGitProcessor(RepositoryProcessor):
    src = None
    path = None

    def __init__(self, path, src):
        self.path = path
        self.src = src

    def IsUpToDate(self):
        return os.path.isdir(self.path)

    def Download(self):
        if os.path.isdir(self.path):
            subprocess.check_call("cd %s && git pull -q" % (self.path), shell = True)
        subprocess.check_call("git clone -q --depth=1 %s %s" % (self.src, self.path), shell = True)

    @staticmethod
    def SanitizeVersion(version):
        pos = version.find('-')
        if pos != -1:
            version = version[0:pos]

        pos = version.find('_')
        if pos != -1:
            version = version[0:pos]

        return version

    def Parse(self):
        result = []

        for category in os.listdir(self.path):
            category_path = os.path.join(self.path, category)
            if not os.path.isdir(category_path):
                continue
            for package in os.listdir(category_path):
                package_path = os.path.join(category_path, package)
                if not os.path.isdir(package_path):
                    continue

                maxversion = None
                bestebuild = None
                for ebuild in os.listdir(package_path):
                    if not ebuild.endswith(".ebuild"):
                        continue
                    ebuild_path = os.path.join(package_path, ebuild)

                    version = ebuild[len(package)+1:-7]

                    if maxversion is None or (version != "9999" and (maxversion == "9999" or parse_version(version) > parse_version(maxversion))):
                        maxversion = version
                        bestebuild = ebuild

                if not maxversion is None:
                    result.append({
                        'name': package,
                        'version': self.SanitizeVersion(maxversion),
                        'category': category,
                    })

        return result
