# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repologyapp.config import config
from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/repository/<repo>')
def repository(repo: str) -> Any:
    autorefresh = flask.request.args.to_dict().get('autorefresh')

    if repo not in repometadata.all_names():
        flask.abort(404)
        #return (flask.render_template('repository-404.html', repo=repo), 404)
    if repo not in repometadata.active_names():
        # HTTP code is intentionally 404
        return (flask.render_template('repository-410.html', repo=repo, repo_info=get_db().get_repository_information(repo)), 404)

    return flask.render_template(
        'repository.html',
        repo=repo,
        repo_info=get_db().get_repository_information(repo),
        autorefresh=autorefresh
    )


@ViewRegistrar('/repository/<repo>/problems')
def repository_problems(repo: str) -> Any:
    if repo not in repometadata.active_names():
        flask.abort(404)

    return flask.render_template('repository-problems.html', repo=repo, problems=get_db().get_repository_problems(repo, config['PROBLEMS_PER_PAGE']))
