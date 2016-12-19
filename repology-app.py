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
from flask import Flask
from math import sqrt

from repology.database import *
from repology.repoman import RepositoryManager
from repology.package import *
from repology.packageproc import *
from repology.metapackageproc import *

# globals
app = Flask(__name__)

app.config.from_pyfile('repology.conf.default')
app.config.from_pyfile('repology.conf', silent=True)
app.config.from_envvar('REPOLOGY_SETTINGS', silent=True)

repoman = RepositoryManager("dummy") # XXX: should not construct fetchers and parsers here

# globals
def SpanTrim(value, maxlength):
    # support lists as well
    if type(value) is list:
        return [SpanTrim(v, maxlength) for v in value]

    if len(value) <= maxlength:
        return value

    # no point in leaving dot just before ellipsis
    trimmed = value[0:maxlength-2]
    while trimmed.endswith('.'):
        trimmed = trimmed[0:-1]

    # we assume ellipsis take ~2 char width
    return "<span title=\"%s\">%s…</span>" % (value, trimmed)

def Clamp(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

def Split(value, sep):
    return value.split(sep)

def NewFormat(value, *args, **kwargs):
    return value.format(**kwargs) if kwargs else value.format(*args)

def PackageVersionClass2CSSClass(value):
    if value == PackageVersionClass.newest:
        return 'good'
    elif value == PackageVersionClass.outdated:
        return 'bad'
    elif value == PackageVersionClass.ignored:
        return 'ignore'

def RepositoryVersionClass2CSSClass(value):
    if value == RepositoryVersionClass.newest:
        return 'good'
    elif value == RepositoryVersionClass.outdated:
        return 'bad'
    elif value == RepositoryVersionClass.mixed:
        return 'multi'
    elif value == RepositoryVersionClass.ignored:
        return 'ignore'
    elif value == RepositoryVersionClass.lonely:
        return 'lonely'

def url_for_self(**args):
    return flask.url_for(flask.request.endpoint, **dict(flask.request.view_args, **args))

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.filters['spantrim'] = SpanTrim
app.jinja_env.filters['clamp'] = Clamp
app.jinja_env.filters['sqrt'] = sqrt
app.jinja_env.filters['split'] = Split
app.jinja_env.filters['newformat'] = NewFormat
app.jinja_env.filters['packageversionclass2css'] = PackageVersionClass2CSSClass
app.jinja_env.filters['repositoryversionclass2css'] = RepositoryVersionClass2CSSClass
app.jinja_env.globals['url_for_self'] = url_for_self
app.jinja_env.globals['next_letter'] = lambda letter : chr(ord(letter) + 1)
app.jinja_env.globals['PER_PAGE'] = app.config['PER_PAGE']
app.jinja_env.globals['REPOLOGY_HOME'] = app.config['REPOLOGY_HOME']

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
        output['www'] = package.homepage,
    if package.comment:
        output['summary'] = package.comment,
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

def metapackages_generic(bound, *filters, template='metapackages.html'):
    namefilter = bound_to_filter(bound)

    reponames = repoman.GetNames(app.config['REPOSITORIES'])

    packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), *filters, limit=app.config['PER_PAGE'])

    # on empty result, fallback to show first, last set of results
    if not packages:
        if bound and bound.startswith('<'):
            namefilter = NameStartingQueryFilter()
        else:
            namefilter = NameBeforeQueryFilter()
        packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), *filters, limit=app.config['PER_PAGE'])

    firstname, lastname = get_packages_name_range(packages)

    summaries = MetapackagesToMetasummaries(PackagesToMetapackages(packages))

    return flask.render_template(
        template,
        reponames=reponames,
        summaries=summaries,
        repometadata=repoman.GetMetadata(),
        firstname=firstname,
        lastname=lastname
    )

def repositories_generic(template='repositories.html'):
    return flask.render_template(template,
        reponames=repoman.GetNames(app.config['REPOSITORIES']),
        repometadata=repoman.GetMetadata(),
    )

@app.route("/") # XXX: redirect to metapackages/all?
@app.route("/metapackages/") # XXX: redirect to metapackages/all?
@app.route("/metapackages/all/")
@app.route("/metapackages/all/<bound>/")
def metapackages_all(bound=None):
    return metapackages_generic(bound)

@app.route("/metapackages/unique/")
@app.route("/metapackages/unique/<bound>/")
def metapackages_unique(bound=None):
    return metapackages_generic(bound, InNumFamiliesQueryFilter(less=1))

@app.route("/metapackages/widespread/")
@app.route("/metapackages/widespread/<bound>/")
def metapackages_widespread(bound=None):
    return metapackages_generic(bound, InNumFamiliesQueryFilter(more=10))

@app.route("/metapackages/in-repo/")
@app.route("/metapackages/in-repo/<repo>/")
@app.route("/metapackages/in-repo/<repo>/<bound>/")
def metapackages_in_repo(repo=None, bound=None):
    if repo:
        return metapackages_generic(bound, InRepoQueryFilter(repo))
    else:
        return repositories_generic()

@app.route("/metapackages/outdated-in-repo/")
@app.route("/metapackages/outdated-in-repo/<repo>/")
@app.route("/metapackages/outdated-in-repo/<repo>/<bound>/")
def metapackages_outdated_in_repo(repo=None, bound=None):
    if repo:
        return metapackages_generic(bound, OutdatedInRepoQueryFilter(repo))
    else:
        return repositories_generic()

@app.route("/metapackages/not-in-repo/")
@app.route("/metapackages/not-in-repo/<repo>/")
@app.route("/metapackages/not-in-repo/<repo>/<bound>/")
def metapackages_not_in_repo(repo=None, bound=None):
    if repo:
        return metapackages_generic(bound, NotInRepoQueryFilter(repo))
    else:
        return repositories_generic()

@app.route("/metapackages/candidates-for-repo/")
@app.route("/metapackages/candidates-for-repo/<repo>/")
@app.route("/metapackages/candidates-for-repo/<repo>/<bound>/")
def metapackages_candidates_for_repo(repo=None, bound=None):
    if repo:
        return metapackages_generic(bound, NotInRepoQueryFilter(repo), InNumFamiliesQueryFilter(more=5))
    else:
        return repositories_generic()

@app.route("/metapackages/unique-in-repo/")
@app.route("/metapackages/unique-in-repo/<repo>/")
@app.route("/metapackages/unique-in-repo/<repo>/<bound>/")
def metapackages_unique_in_repo(repo=None, bound=None):
    if repo:
        return metapackages_generic(bound, InRepoQueryFilter(repo), InNumFamiliesQueryFilter(less=1))
    else:
        return repositories_generic()

@app.route("/metapackages/by-maintainer/<maintainer>/")
@app.route("/metapackages/by-maintainer/<maintainer>/<bound>/")
def metapackages_by_maintainer(maintainer, bound=None):
    return metapackages_generic(bound, MaintainerQueryFilter(maintainer))

@app.route("/metapackages/outdated-by-maintainer/<maintainer>/")
@app.route("/metapackages/outdated-by-maintainer/<maintainer>/<bound>/")
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return metapackages_generic(bound, MaintainerOutdatedQueryFilter(maintainer))

@app.route("/maintainers/")
@app.route("/maintainers/<int:page>/")
def maintainers(page=0):
    maintainers_count = get_db().GetMaintainersCount()
    maintainers = get_db().GetMaintainers(offset = page * app.config['PER_PAGE'], limit = app.config['PER_PAGE'])

    return flask.render_template(
        "maintainers.html",
        maintainers=maintainers,
        page=page,
        num_pages=((maintainers_count + app.config['PER_PAGE'] - 1) // app.config['PER_PAGE'])
    )

@app.route("/metapackage/<name>")
def metapackage(name):
    packages = get_db().GetMetapackage(name)
    if not packages:
        flask.abort(404);

    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    repometadata = repoman.GetMetadata();
    return flask.render_template("package.html", packages=packages, repometadata=repometadata, name=name)

@app.route("/badge/vertical-allrepos/<name>")
def badge_vertical_allrepos(name):
    summaries = PackagesetToSummaries(get_db().GetMetapackage(name))
    repometadata = repoman.GetMetadata();

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

@app.route("/badge/tiny-packages/<name>")
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

@app.route("/badges")
def badges():
    return flask.render_template("badges.html")

@app.route("/statistics")
def statistics():
    return flask.render_template(
        "statistics.html",
        reponames=repoman.GetNames(app.config['REPOSITORIES']),
        repometadata=repoman.GetMetadata(),
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
