# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


@ViewRegistrar('/opensearch/project.xml')
def opensearch_project() -> Any:
    return flask.render_template('opensearch-project.xml'), {'Content-type': 'application/xml'}


@ViewRegistrar('/opensearch/maintainer.xml')
def opensearch_maintainer() -> Any:
    return flask.render_template('opensearch-maintainer.xml'), {'Content-type': 'application/xml'}
