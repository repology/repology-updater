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

from typing import Any

import flask

from repologyapp.db import get_db
from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/log/<run_id>')
def log(run_id: int) -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    run = get_db().get_run(int(run_id))

    if not run:
        flask.abort(404)

    return flask.render_template(
        'log.html',
        run=run,
        lines=get_db().get_log_lines(run_id),
        autorefresh=autorefresh
    )
