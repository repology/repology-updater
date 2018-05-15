# Copyright (C) 2018 Paul Wise <pabs3@bonedaddy.net>
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

import flask

from repologyapp.globals import repometadata, get_db
from repologyapp.view_registry import ViewRegistrar
from werkzeug.routing import BuildError

@ViewRegistrar('/package/<repo>/<package>/<page>')
def package(repo, package, page=None):
    if not repo or repo not in repometadata or not package:
        flask.abort(404)

    metapackages = get_db().get_package_metapackage(package)
    metapackage_count = len(metapackages)

    if metapackage_count == 0:
        flask.abort(404)
    elif metapackage_count == 1:
        page_base = 'metapackage'
        if page:
        	page = '_' + page
        else:
        	page = ''
        page_type = page_base + page
        metapackage = metapackages[0]
        try:
            url = flask.url_for(page_type, name=metapackage)
        except BuildError:
            flask.abort(404)
        return flask.redirect(url, 307)
    else:
        flask.abort(500)
