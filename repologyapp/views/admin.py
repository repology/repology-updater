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

from typing import Any, Callable, Dict

import flask

from repologyapp.config import config
from repologyapp.db import get_db
from repologyapp.template_functions import url_for_self
from repologyapp.view_registry import ViewRegistrar


def unauthorized() -> Any:
    return flask.redirect(flask.url_for('admin'))


@ViewRegistrar('/admin', methods=['GET', 'POST'])
def admin() -> Any:
    if flask.request.method == 'POST':
        if config['ADMIN_PASSWORD'] is None:
            flask.flash('Admin login disabled', 'danger')
        elif flask.request.form.get('password') is None:
            flask.session['admin'] = False
            flask.flash('Logged out successfully', 'success')
        elif flask.request.form.get('password') == config['ADMIN_PASSWORD']:
            flask.session['admin'] = True
            flask.flash('Logged in successfully', 'success')
        else:
            flask.flash('Incorrect admin password', 'danger')

        return flask.redirect(flask.url_for('admin'), 301)

    return flask.render_template('admin.html')


def admin_reports_generic(report_getter: Callable[[], Dict[str, Any]]) -> Any:
    if not flask.session.get('admin'):
        return unauthorized()

    if flask.request.method == 'POST':
        id_ = flask.request.form.get('id')
        reply = flask.request.form.get('reply', '')
        action = flask.request.form.get('action', None)

        if action == 'delete':
            get_db().delete_report(id_)
            flask.flash('Report removed succesfully', 'success')
            return flask.redirect(url_for_self())

        if action == 'accept':
            get_db().update_report(id_, reply, True)
        elif action == 'reject':
            get_db().update_report(id_, reply, False)
        else:
            get_db().update_report(id_, reply, None)

        flask.flash('Report updated succesfully', 'success')
        return flask.redirect(url_for_self())

    return flask.render_template('admin-reports.html', reports=report_getter())


@ViewRegistrar('/admin/reports/unprocessed/', methods=['GET', 'POST'])
def admin_reports_unprocessed() -> Any:
    return admin_reports_generic(lambda: get_db().get_unprocessed_reports(limit=config['REPORTS_PER_PAGE']))  # type: ignore


@ViewRegistrar('/admin/reports/recent/', methods=['GET', 'POST'])
def admin_reports_recent() -> Any:
    return admin_reports_generic(lambda: get_db().get_recently_updated_reports(limit=config['REPORTS_PER_PAGE']))  # type: ignore


@ViewRegistrar('/admin/updates')
def admin_updates() -> Any:
    if not flask.session.get('admin'):
        return unauthorized()

    return flask.render_template(
        'admin-updates.html',
        repos=get_db().get_repositories_update_diagnostics()
    )
