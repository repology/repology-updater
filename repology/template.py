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
import jinja2

def SpanTrim(str, maxlength):
    if len(str) <= maxlength:
        return str

    return "<span title=\"%s\">%s…</span>" % (str, str[0:maxlength])

class Template:
    def __init__(self):
        self.env = jinja2.Environment(
            loader = jinja2.PackageLoader('repology', 'templates'),
            lstrip_blocks = True,
            trim_blocks = True,
        )
        self.env.filters["spantrim"] = SpanTrim

    def Render(self, template, **template_data):
        template = self.env.get_template(template)

        data = template_data.copy()
        data['gentime'] = time.strftime("%Y-%m-%d %H:%M %Z", time.gmtime())

        return template.render(data)

    def RenderToFile(self, template, path, **template_data):
        with open(path, 'w', encoding="utf-8") as file:
            file.write(self.Render(template, **template_data))
