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
from repologyapp.metapackages import MetapackagesFilterInfo, get_packages_name_range, metapackages_to_summary_items
from repologyapp.view_registry import ViewRegistrar

from repology.config import config
from repology.metapackageproc import PackagesToMetapackages
from repology.package import VersionClass
from repology.packageproc import PackagesetSortByVersions


@ViewRegistrar('/metapackages/')
@ViewRegistrar('/metapackages/<bound>/')
def metapackages(bound=None):
    # process search
    filterinfo = MetapackagesFilterInfo()
    filterinfo.ParseFlaskArgs()

    request = filterinfo.GetRequest()
    request.Bound(bound)

    # get packages
    packages = get_db().GetMetapackages(request, limit=config['METAPACKAGES_PER_PAGE'])

    # on empty result, fallback to show first, last set of results
    if not packages:
        request = filterinfo.GetRequest()
        if bound and bound.startswith('..'):
            request.NameTo(None)
        packages = get_db().GetMetapackages(request, limit=config['METAPACKAGES_PER_PAGE'])

    firstname, lastname = get_packages_name_range(packages)

    metapackagedata = metapackages_to_summary_items(PackagesToMetapackages(packages), filterinfo.GetRepo(), filterinfo.GetMaintainer())

    return flask.render_template(
        'metapackages.html',
        firstname=firstname,
        lastname=lastname,
        search=filterinfo.GetDict(),
        advanced=filterinfo.IsAdvanced(),
        metapackagedata=metapackagedata,
        repo=filterinfo.GetRepo(),
        maintainer=filterinfo.GetMaintainer()
    )


@ViewRegistrar('/metapackages/all/')
@ViewRegistrar('/metapackages/all/<bound>/')
def metapackages_all(bound=None):
    return flask.redirect(flask.url_for('metapackages', bound=bound, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/unique/')
@ViewRegistrar('/metapackages/unique/<bound>/')
def metapackages_unique(bound=None):
    return flask.redirect(flask.url_for('metapackages', bound=bound, maxspread=1, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/widespread/')
@ViewRegistrar('/metapackages/widespread/<bound>/')
def metapackages_widespread(bound=None):
    return flask.redirect(flask.url_for('metapackages', bound=bound, minspread=10, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/in-repo/<repo>/')
@ViewRegistrar('/metapackages/in-repo/<repo>/<bound>/')
def metapackages_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.redirect(flask.url_for('metapackages', bound=bound, inrepo=repo, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/outdated-in-repo/<repo>/')
@ViewRegistrar('/metapackages/outdated-in-repo/<repo>/<bound>/')
def metapackages_outdated_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.redirect(flask.url_for('metapackages', bound=bound, inrepo=repo, outdated=1, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/not-in-repo/<repo>/')
@ViewRegistrar('/metapackages/not-in-repo/<repo>/<bound>/')
def metapackages_not_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.redirect(flask.url_for('metapackages', bound=bound, notinrepo=repo, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/candidates-for-repo/<repo>/')
@ViewRegistrar('/metapackages/candidates-for-repo/<repo>/<bound>/')
def metapackages_candidates_for_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.redirect(flask.url_for('metapackages', bound=bound, inrepo=repo, minspread=5, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/unique-in-repo/<repo>/')
@ViewRegistrar('/metapackages/unique-in-repo/<repo>/<bound>/')
def metapackages_unique_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.redirect(flask.url_for('metapackages', bound=bound, inrepo=repo, maxspread=1, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/by-maintainer/<maintainer>/')
@ViewRegistrar('/metapackages/by-maintainer/<maintainer>/<bound>/')
def metapackages_by_maintainer(maintainer, bound=None):
    return flask.redirect(flask.url_for('metapackages', bound=bound, maintainer=maintainer, search=flask.request.args.to_dict().get('search')), 301)


@ViewRegistrar('/metapackages/outdated-by-maintainer/<maintainer>/')
@ViewRegistrar('/metapackages/outdated-by-maintainer/<maintainer>/<bound>/')
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return flask.redirect(flask.url_for('metapackages', bound=bound, maintainer=maintainer, outdated=1, search=flask.request.args.to_dict().get('search')), 301)
