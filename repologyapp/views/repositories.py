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

import flask

from repologyapp.globals import *
from repologyapp.view_registry import ViewRegistrar

from repology.config import config


@ViewRegistrar('/repositories/')
def repositories():
    return flask.render_template('repositories.html')


@ViewRegistrar('/repository/<repo>')
def repository(repo):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.render_template(
        'repository.html',
        repo=repo,
        repo_info=get_db().GetRepository(repo)
    )


@ViewRegistrar('/repository/<repo>/problems')
def repository_problems(repo):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.render_template('repository-problems.html', repo=repo, problems=get_db().GetProblems(repo=repo, limit=config['PROBLEMS_PER_PAGE']))
