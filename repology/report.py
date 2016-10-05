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


class ReportProducer:
    def __init__(self, template, templatename):
        self.template = template
        self.templatename = templatename

    def RenderFilesPaginated(self, path, metapackages, reponames, perpage, **extradata):
        numpages = (len(metapackages) + perpage - 1) // perpage

        for page in range(0, numpages):
            pagepath = "%s.%d.html" % (path, page)

            self.RenderToFile(
                pagepath,
                metapackages[page * perpage:page * perpage + perpage],
                reponames,
                page=page,
                numpages=numpages,
                basename=os.path.basename(path),
                **extradata
            )

    def Prepare(self, metapackages, reponames, **template_data):
        data = {
            'reponames': reponames,
            'packages': metapackages
        }
        data.update(template_data)
        return data

    def Render(self, metapackages, reponames, **template_data):
        return self.template.Render(self.templatename, **self.Prepare(metapackages, reponames, **template_data))

    def RenderToFile(self, path, metapackages, reponames, **template_data):
        self.template.RenderToFile(self.templatename, path, **self.Prepare(metapackages, reponames, **template_data))
