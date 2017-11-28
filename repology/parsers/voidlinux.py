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
import collections
import subprocess

from repology.package import Package
from repology.version import VersionCompare

SEP = ":\t"

class VoidLinuxGitParser():

    def Parse(self, path):
        packages = []

        source_path = os.path.join(path, 'srcpkgs')
        xbps_src_path = os.path.join(path, 'xbps-src')
        for package_name in os.listdir(source_path):
            result = subprocess.run(
                [xbps_src_path, "show", package_name],
                stdout=subprocess.PIPE,
                encoding="UTF-8"
            )
        
            if result.returncode != 0:
                print("Failed to read template for {}".format(package_name), file=sys.stderr)
                continue
        
            variables = collections.defaultdict(list)
            for line in result.stdout.splitlines():
                variable, *rest = line.split(SEP)
                if rest: variables[variable].append(SEP.join(rest))
                                    
            pkg = Package()
            pkg.name = variables["pkgname"][0]
            pkg.version = variables["version"][0] + "-" + variables["revision"][0]
            pkg.licenses = [l.strip() for l in variables["License(s)"][0].split(',')]
            pkg.comment = variables["short_desc"][0]
            pkg.homepage = variables["Upstream URL"][0]
            pkg.downloads = variables["distfiles"]

            packages.append(pkg)

        return packages

