# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repologyapp.config import config
from repologyapp.db import get_db
from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/experimental/')
def experimental():
    return flask.render_template('experimental.html')


@ViewRegistrar('/experimental/turnover/metapackages')
def metapackages_turnover():
    return flask.render_template(
        'metapackages-turnover.html',
        added=get_db().get_recently_added_metapackages(config['TURNOVER_PER_PAGE']),
        removed=get_db().get_recently_removed_metapackages(config['TURNOVER_PER_PAGE'])
    )


@ViewRegistrar('/experimental/turnover/maintainers')
def maintainers_turnover():
    return flask.render_template(
        'maintainers-turnover.html',
        added=get_db().get_recently_added_maintainers(config['TURNOVER_PER_PAGE']),
        removed=get_db().get_recently_removed_maintainers(config['TURNOVER_PER_PAGE'])
    )


@ViewRegistrar('/experimental/raising')
def raising():
    return flask.render_template(
        'raising.html',
        packages1=get_db().get_raising_metapackages1(config['METAPACKAGES_PER_PAGE']),
        packages2=get_db().get_raising_metapackages2(config['METAPACKAGES_PER_PAGE']),
    )


@ViewRegistrar('/experimental/distromap')
def distromap():
    return flask.render_template('distromap.html')
