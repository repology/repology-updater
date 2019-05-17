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

from typing import Any

import flask

from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/news')
def news() -> Any:
    return flask.render_template('news.html')


@ViewRegistrar('/about')
def about() -> Any:
    return flask.render_template('about.html')


@ViewRegistrar('/docs')
def docs() -> Any:
    return flask.render_template('docs.html')


@ViewRegistrar('/addrepo')
def addrepo() -> Any:
    return flask.render_template('addrepo.html')


@ViewRegistrar('/bots')
def bots() -> Any:
    return flask.render_template('bots.html')


@ViewRegistrar('/favicon.ico')
def favicon() -> Any:
    return flask.current_app.send_static_file('repology.v1.ico')
