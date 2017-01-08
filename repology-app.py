#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json
import flask

from repology.database import Database
from repology.queryfilters import *
from repology.repoman import RepositoryManager
from repology.packageproc import *
from repology.metapackageproc import *
from repology.template_helpers import *

# create application and handle configuration
app = flask.Flask(__name__)

app.config.from_pyfile('repology.conf.default')
app.config.from_pyfile('repology.conf', silent=True)
app.config.from_envvar('REPOLOGY_CONFIG', silent=True)

# global repology objects
repoman = RepositoryManager(app.config['REPOS_PATH'], "dummy") # XXX: should not construct fetchers and parsers here
repometadata = repoman.GetMetadata();

# templates: tuning
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# templates: custom filters
app.jinja_env.filters['pkg_format'] = pkg_format
app.jinja_env.filters['css_for_package_versionclass'] = css_for_package_versionclass
app.jinja_env.filters['css_for_summary_versionclass'] = css_for_summary_versionclass
app.jinja_env.filters['maintainer_to_link'] = maintainer_to_link

# templates: custom tests
app.jinja_env.tests['for_page'] = for_page

# templates: custom global functions
app.jinja_env.globals['url_for_self'] = url_for_self

# templates: custom global data
app.jinja_env.globals['PER_PAGE'] = app.config['PER_PAGE']
app.jinja_env.globals['REPOLOGY_HOME'] = app.config['REPOLOGY_HOME']
app.jinja_env.globals['repometadata'] = repometadata

def get_db():
    if not hasattr(flask.g, 'database'):
        flask.g.database = Database(app.config['DSN'], readonly=True)
    return flask.g.database

# helpers
def api_v1_package_to_json(package):
    output = {
        field: getattr(package, field)
            for field in (
                'repo',
                'name',
                'version',
                'origversion',
                'maintainers',
                #'category',
                #'comment',
                #'homepage',
                'licenses',
                'downloads')
            if getattr(package, field)
    }

    # XXX: these tweaks should be implemented in core
    if package.homepage:
        output['www'] = [ package.homepage ]
    if package.comment:
        output['summary'] = package.comment
    if package.category:
        output['categories'] = [ package.category ]

    return output

def api_v1_metapackages_generic(bound, *filters):
    metapackages = PackagesToMetapackages(
        get_db().GetMetapackages(
            bound_to_filter(bound),
            *filters,
            limit=app.config['PER_PAGE']
        )
    )

    metapackages = { metapackage_name: list(map(api_v1_package_to_json, packageset)) for metapackage_name, packageset in metapackages.items() }

    return (
        json.dumps(metapackages),
        {'Content-type': 'application/json'}
    )

def bound_to_filter(bound):
    if bound and bound.startswith('<'):
        return NameBeforeQueryFilter(bound[1:])
    elif bound and bound.startswith('>'):
        return NameAfterQueryFilter(bound[1:])
    else:
        return NameStartingQueryFilter(bound)

def get_packages_name_range(packages):
    firstname, lastname = None, None

    if packages:
        firstname = lastname = packages[0].effname
        for package in packages[1:]:
            lastname = max(lastname, package.effname)
            firstname = min(firstname, package.effname)

    return firstname, lastname

def metapackages_generic(bound, *filters, template='metapackages.html', extravars=None):
    namefilter = bound_to_filter(bound)

    reponames = repoman.GetNames(app.config['REPOSITORIES'])

    # process search
    search = flask.request.args.to_dict().get('search')
    searchfilter = NameSubstringQueryFilter(search) if search else None

    # get packages
    packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), searchfilter, *filters, limit=app.config['PER_PAGE'])

    # on empty result, fallback to show first, last set of results
    if not packages:
        if bound and bound.startswith('<'):
            namefilter = NameStartingQueryFilter()
        else:
            namefilter = NameBeforeQueryFilter()
        packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), searchfilter, *filters, limit=app.config['PER_PAGE'])

    firstname, lastname = get_packages_name_range(packages)

    summaries = MetapackagesToMetasummaries(PackagesToMetapackages(packages))

    return flask.render_template(
        template,
        reponames=reponames,
        summaries=summaries,
        firstname=firstname,
        lastname=lastname,
        search=search,
        **(extravars if extravars else {})
    )

@app.route("/") # XXX: redirect to metapackages/all?
@app.route("/metapackages/") # XXX: redirect to metapackages/all?
@app.route("/metapackages/all/")
@app.route("/metapackages/all/<bound>/")
def metapackages_all(bound=None):
    return metapackages_generic(
        bound,
        template="metapackages-all.html"
    )

@app.route("/metapackages/unique/")
@app.route("/metapackages/unique/<bound>/")
def metapackages_unique(bound=None):
    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(less=1),
        template="metapackages-unique.html"
    )

@app.route("/metapackages/widespread/")
@app.route("/metapackages/widespread/<bound>/")
def metapackages_widespread(bound=None):
    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(more=10),
        template="metapackages-widespread.html"
    )

@app.route("/metapackages/in-repo/<repo>/")
@app.route("/metapackages/in-repo/<repo>/<bound>/")
def metapackages_in_repo(repo, bound=None):
    if not repo or not repo in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        template="metapackages-in-repo.html",
        extravars={'repo': repo}
    )

@app.route("/metapackages/outdated-in-repo/<repo>/")
@app.route("/metapackages/outdated-in-repo/<repo>/<bound>/")
def metapackages_outdated_in_repo(repo, bound=None):
    if not repo or not repo in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        OutdatedInRepoQueryFilter(repo),
        template="metapackages-outdated-in-repo.html",
        extravars={'repo': repo}
    )

@app.route("/metapackages/not-in-repo/<repo>/")
@app.route("/metapackages/not-in-repo/<repo>/<bound>/")
def metapackages_not_in_repo(repo, bound=None):
    if not repo or not repo in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        NotInRepoQueryFilter(repo),
        template="metapackages-not-in-repo.html",
        extravars={'repo': repo}
    )

@app.route("/metapackages/candidates-for-repo/<repo>/")
@app.route("/metapackages/candidates-for-repo/<repo>/<bound>/")
def metapackages_candidates_for_repo(repo, bound=None):
    if not repo or not repo in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(more=5),
        template="metapackages-candidates-for-repo.html",
        extravars={'repo': repo}
    )

@app.route("/metapackages/unique-in-repo/<repo>/")
@app.route("/metapackages/unique-in-repo/<repo>/<bound>/")
def metapackages_unique_in_repo(repo, bound=None):
    if not repo or not repo in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        InNumFamiliesQueryFilter(less=1),
        template="metapackages-unique-in-repo.html",
        extravars={'repo': repo}
    )

@app.route("/metapackages/by-maintainer/<maintainer>/")
@app.route("/metapackages/by-maintainer/<maintainer>/<bound>/")
def metapackages_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerQueryFilter(maintainer),
        template="metapackages-by-maintainer.html",
        extravars={'maintainer': maintainer}
    )

@app.route("/metapackages/outdated-by-maintainer/<maintainer>/")
@app.route("/metapackages/outdated-by-maintainer/<maintainer>/<bound>/")
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerOutdatedQueryFilter(maintainer),
        template="metapackages-outdated-by-maintainer.html",
        extravars={'maintainer': maintainer}
    )

@app.route("/maintainers/")
@app.route("/maintainers/<page>/")
def maintainers(page=None):
    maintainers = get_db().GetMaintainersByLetter(page) # handles page sanity inside

    return flask.render_template(
        "maintainers.html",
        maintainers=maintainers,
        page=page
    )

@app.route("/repositories/")
def repositories():
    return flask.render_template(
        "repositories.html",
        reponames=repoman.GetNames(app.config['REPOSITORIES']),
    )

@app.route("/metapackage/<name>")
def metapackage(name):
    # metapackage landing page; just redirect to packages, may change in future
    return flask.redirect(flask.url_for('metapackage_packages', 303))

@app.route("/metapackage/<name>/packages")
def metapackage_packages(name):
    packages = get_db().GetMetapackage(name)
    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    return flask.render_template("metapackage-packages.html", packages=packages, name=name)

@app.route("/metapackage/<name>/information")
def metapackage_information(name):
    packages = get_db().GetMetapackage(name)
    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    return flask.render_template("metapackage-information.html", packages=packages, name=name)

@app.route("/metapackage/<name>/badges")
def metapackage_badges(name):
    return flask.render_template("metapackage-badges.html", name=name)

@app.route("/badge/vertical-allrepos/<name>.svg")
def badge_vertical_allrepos(name):
    summaries = PackagesetToSummaries(get_db().GetMetapackage(name))

    repostates = []
    for reponame, summary in summaries.items():
        repostates.append({
            'name': repometadata[reponame]['desc'],
            'version': summary['version'],
            'versionclass': summary['versionclass']
        })

    return (
        flask.render_template(
            "badge-vertical.svg",
            repositories=sorted(repostates, key=lambda repo: repo['name']),
            name=name
        ),
        {'Content-type': 'image/svg+xml'}
    )

@app.route("/badge/tiny-packages/<name>.svg")
def badge_tiny_packages(name):
    return (
        flask.render_template(
            "badge-tiny.svg",
            name=name,
            num_packages=len(PackagesetToSummaries(get_db().GetMetapackage(name)))
        ),
        {'Content-type': 'image/svg+xml'}
    )

@app.route("/news")
def news():
    return flask.render_template("news.html")

@app.route("/about")
def about():
    return flask.render_template("about.html")

@app.route("/statistics")
def statistics():
    return flask.render_template(
        "statistics.html",
        reponames=repoman.GetNames(app.config['REPOSITORIES']),
        repostats=get_db().GetRepositories(),
        num_metapackages=get_db().GetMetapackagesCount()
    )

@app.route("/api/v1/metapackage/<name>")
def api_v1_metapackage(name):
    return (
        json.dumps(list(map(
            api_v1_package_to_json,
            get_db().GetMetapackage(name)
        ))),
        {'Content-type': 'application/json'}
    )

@app.route("/api")
@app.route("/api/v1")
def api_v1():
    return flask.render_template("api.html")

@app.route("/api/v1/metapackages/")
@app.route("/api/v1/metapackages/all/")
@app.route("/api/v1/metapackages/all/<bound>/")
def api_v1_metapackages_all(bound=None):
    return api_v1_metapackages_generic(bound)

@app.route("/api/v1/metapackages/unique/")
@app.route("/api/v1/metapackages/unique/<bound>/")
def api_v1_metapackages_unique(bound=None):
    return api_v1_metapackages_generic(bound, InNumFamiliesQueryFilter(less=1))

@app.route("/api/v1/metapackages/in-repo/<repo>/")
@app.route("/api/v1/metapackages/in-repo/<repo>/<bound>/")
def api_v1_metapackages_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, InRepoQueryFilter(repo))

@app.route("/api/v1/metapackages/outdated-in-repo/<repo>/")
@app.route("/api/v1/metapackages/outdated-in-repo/<repo>/<bound>/")
def api_v1_metapackages_outdated_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, OutdatedInRepoQueryFilter(repo))

@app.route("/api/v1/metapackages/not-in-repo/<repo>/")
@app.route("/api/v1/metapackages/not-in-repo/<repo>/<bound>/")
def api_v1_metapackages_not_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, NotInRepoQueryFilter(repo))

@app.route("/api/v1/metapackages/candidates-in-repo/<repo>/")
@app.route("/api/v1/metapackages/candidates-in-repo/<repo>/<bound>/")
def api_v1_metapackages_candidates_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, InNumFamiliesQueryFilter(more=5))

@app.route("/api/v1/metapackages/unique-in-repo/<repo>/")
@app.route("/api/v1/metapackages/unique-in-repo/<repo>/<bound>/")
def api_v1_metapackages_unique_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, InNumFamiliesQueryFilter(less=1))

@app.route("/api/v1/metapackages/by-maintainer/<maintainer>/")
@app.route("/api/v1/metapackages/by-maintainer/<maintainer>/<bound>/")
def api_v1_metapackages_by_maintainer(maintainer, bound=None):
    return api_v1_metapackages_generic(bound, MaintainerQueryFilter(maintainer))

@app.route("/api/v1/metapackages/outdated-by-maintainer/<maintainer>/")
@app.route("/api/v1/metapackages/outdated-by-maintainer/<maintainer>/<bound>/")
def api_v1_metapackages_outdated_by_maintainer(maintainer, bound=None):
    return api_v1_metapackages_generic(bound, MaintainerOutdatedQueryFilter(maintainer))

if __name__ == "__main__":
    app.run()
