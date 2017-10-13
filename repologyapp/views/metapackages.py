#!/usr/bin/env python3
#
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
from repologyapp.metapackages import bound_to_filter, get_packages_name_range, metapackages_to_summary_items
from repologyapp.view_registry import ViewRegistrar

import repology.config
from repology.queryfilters import *
from repology.packageproc import PackagesetSortByVersions
from repology.metapackageproc import PackagesToMetapackages
from repology.package import VersionClass


def metapackages_generic(bound, *filters, template='metapackages.html', repo=None, maintainer=None):
    namefilter = bound_to_filter(bound)

    # process search
    search = flask.request.args.to_dict().get('search')
    search = None if search is None else search.strip()
    searchfilter = NameSubstringQueryFilter(search) if search else None

    # get packages
    packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), searchfilter, *filters, limit=repology.config.METAPACKAGES_PER_PAGE)

    # on empty result, fallback to show first, last set of results
    if not packages:
        if bound and bound.startswith('<'):
            namefilter = NameStartingQueryFilter()
        else:
            namefilter = NameBeforeQueryFilter()
        packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), searchfilter, *filters, limit=repology.config.METAPACKAGES_PER_PAGE)

    firstname, lastname = get_packages_name_range(packages)

    metapackagedata = metapackages_to_summary_items(PackagesToMetapackages(packages), repo, maintainer)

    return flask.render_template(
        template,
        firstname=firstname,
        lastname=lastname,
        search=search,
        metapackagedata=metapackagedata,
        repo=repo,
        maintainer=maintainer
    )


@ViewRegistrar('/metapackages/')  # XXX: redirect to metapackages/all?
@ViewRegistrar('/metapackages/all/')
@ViewRegistrar('/metapackages/all/<bound>/')
def metapackages_all(bound=None):
    return metapackages_generic(
        bound,
        template='metapackages-all.html'
    )


@ViewRegistrar('/metapackages/unique/')
@ViewRegistrar('/metapackages/unique/<bound>/')
def metapackages_unique(bound=None):
    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(less=1),
        template='metapackages-unique.html'
    )


@ViewRegistrar('/metapackages/widespread/')
@ViewRegistrar('/metapackages/widespread/<bound>/')
def metapackages_widespread(bound=None):
    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(more=10),
        template='metapackages-widespread.html'
    )


@ViewRegistrar('/metapackages/in-repo/<repo>/')
@ViewRegistrar('/metapackages/in-repo/<repo>/<bound>/')
def metapackages_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        template='metapackages-in-repo.html',
        repo=repo,
    )


@ViewRegistrar('/metapackages/outdated-in-repo/<repo>/')
@ViewRegistrar('/metapackages/outdated-in-repo/<repo>/<bound>/')
def metapackages_outdated_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        OutdatedInRepoQueryFilter(repo),
        template='metapackages-outdated-in-repo.html',
        repo=repo,
    )


@ViewRegistrar('/metapackages/not-in-repo/<repo>/')
@ViewRegistrar('/metapackages/not-in-repo/<repo>/<bound>/')
def metapackages_not_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        NotInRepoQueryFilter(repo),
        template='metapackages-not-in-repo.html',
        repo=repo,
    )


@ViewRegistrar('/metapackages/candidates-for-repo/<repo>/')
@ViewRegistrar('/metapackages/candidates-for-repo/<repo>/<bound>/')
def metapackages_candidates_for_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        NotInRepoQueryFilter(repo),
        InNumFamiliesQueryFilter(more=5),
        template='metapackages-candidates-for-repo.html',
        repo=repo,
    )


@ViewRegistrar('/metapackages/unique-in-repo/<repo>/')
@ViewRegistrar('/metapackages/unique-in-repo/<repo>/<bound>/')
def metapackages_unique_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        InNumFamiliesQueryFilter(less=1),
        template='metapackages-unique-in-repo.html',
        repo=repo,
    )


@ViewRegistrar('/metapackages/by-maintainer/<maintainer>/')
@ViewRegistrar('/metapackages/by-maintainer/<maintainer>/<bound>/')
def metapackages_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerQueryFilter(maintainer),
        template='metapackages-by-maintainer.html',
        maintainer=maintainer,
    )


@ViewRegistrar('/metapackages/outdated-by-maintainer/<maintainer>/')
@ViewRegistrar('/metapackages/outdated-by-maintainer/<maintainer>/<bound>/')
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerOutdatedQueryFilter(maintainer),
        template='metapackages-outdated-by-maintainer.html',
        maintainer=maintainer,
    )
