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
from math import sqrt

def SpanTrim(value, maxlength):
    if len(value) <= maxlength:
        return value

    # no point in leaving dot just before ellipsis
    trimmed = value[0:maxlength-2]
    while trimmed.endswith('.'):
        trimmed = trimmed[0:-1]

    # we assume ellipsis take ~2 char width
    return "<span title=\"%s\">%s…</span>" % (value, trimmed)

def Clamp(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

class Template:
    def __init__(self):
        self.env = jinja2.Environment(
            loader = jinja2.PackageLoader('repology', 'templates'),
            lstrip_blocks = True,
            trim_blocks = True,
        )
        self.env.filters["spantrim"] = SpanTrim
        self.env.filters["clamp"] = Clamp
        self.env.filters["sqrt"] = sqrt
        self.template_cache = {}

    def Render(self, template, **template_data):
        if not template in self.template_cache:
            self.template_cache[template] = self.env.get_template(template)

        data = template_data.copy()
        data['gentime'] = time.strftime("%Y-%m-%d %H:%M %Z", time.gmtime())

        return self.template_cache[template].render(data)

    def RenderToFile(self, template, path, **template_data):
        with open(path, 'w', encoding="utf-8") as file:
            file.write(self.Render(template, **template_data))
