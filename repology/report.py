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

import time
import os

from .util import VersionCompare

class ReportProducer:
    def __init__(self, template, templatename):
        self.template = template
        self.templatename = templatename

    def RenderFilesPaginated(self, path, packages, reponames, perpage, **extradata):
        keys = sorted(packages.keys())

        numpages = (len(keys) + perpage - 1) // perpage

        for page in range(0, numpages):
            pagepath = "%s.%d.html" % (path, page)

            self.RenderToFile(
                pagepath,
                {k:packages[k] for k in keys[page * perpage:page * perpage + perpage]},
                reponames,
                page = page,
                numpages = numpages,
                basename = os.path.basename(path),
                **extradata
            )

    def Prepare(self, packages, reponames, **template_data):
        data = {
            'reponames': reponames,
            'repositories': {},
            'packages': [],
            'gentime': time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        }

        data.update(template_data)

        for reponame in reponames:
            data['repositories'][reponame] = {}

        for pkgname in sorted(packages.keys()):
            metapackage = packages[pkgname]

            bestversion, _, _ = metapackage.GetMaxVersion()

            template_package = {
                'name': pkgname,
                'byrepo': {}
            }

            for reponame in metapackage.GetRepos():
                # packages for this repository
                repopackages = metapackage.Get(reponame)

                # determine versions
                repominversion, repomaxversion = metapackage.GetVersionRangeForRepo(reponame)

                versionclass = 'bad'
                if metapackage.GetNumRepos() == 1:
                    versionclass = 'lonely'
                elif bestversion is None:
                    versionclass = 'good'
                elif VersionCompare(repomaxversion, bestversion) > 0: # due to ignore
                    versionclass = 'ignore'
                elif VersionCompare(repomaxversion, bestversion) >= 0:
                    if VersionCompare(repominversion, bestversion) == 0:
                        versionclass = 'good'
                    else:
                        versionclass = 'multi'

                template_package['byrepo'][reponame] = {
                    'version': repomaxversion,
                    'class': versionclass,
                    'numpackages': len(repopackages)
                }

            data['packages'].append(template_package)

        return data

    def Render(self, packages, reponames, **template_data):
        return self.template.Render(self.templatename, **self.Prepare(packages, reponames, **template_data))

    def RenderToFile(self, path, packages, reponames, **template_data):
        self.template.RenderToFile(self.templatename, path, **self.Prepare(packages, reponames, **template_data))
