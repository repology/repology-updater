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

# settings
PER_PAGE = 500
REPOSITORIES = ['production']

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

app = Flask(__name__)
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

database = Database("dbname=repology user=repology password=repology", readonly=True)
repoman = RepositoryManager("dummy") # XXX: should not construct fetchers and parsers here

# helpers
def api_v1_package_to_json(package):
    return {
        field: getattr(package, field)
        for field in (
            'repo',
            'name',
            'version',
            'origversion',
            'maintainers',
            'category',
            'comment',
            'homepage',
            'licenses',
            'downloads',
            'ignore')
        if getattr(package, field)
    }

def api_v1_metapackages_generic(bound, *filters):
    return (
        json.dumps(list(map(
            api_v1_package_to_json,
            database.GetMetapackages(
                bound_to_filter(bound),
                *filters,
                limit=PER_PAGE
            )
        ))),
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

def metapackages_generic(bound, template='metapackages.html', *filters):
    namefilter = bound_to_filter(bound)

    reponames = repoman.GetNames(REPOSITORIES)

    packages = database.GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), *filters, limit=PER_PAGE)

    # on empty result, fallback to show first, last set of results
    if not packages:
        if bound and bound.startswith('<'):
            namefilter = NameStartingQueryFilter()
        else:
            namefilter = NameBeforeQueryFilter()
        packages = database.GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), *filters, limit=PER_PAGE)

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

@app.route("/")
@app.route("/metapackages/all/")
@app.route("/metapackages/all/<bound>")
def metapackages_all(bound=None):
    return metapackages_generic(bound)

@app.route("/metapackages/in-repo/<repo>/")
@app.route("/metapackages/in-repo/<repo>/<bound>")
def metapackages_in_repo(repo, bound=None):
    return metapackages_generic(bound, InRepoQueryFilter(repo))

@app.route("/metapackages/not-in-repo/<repo>/")
@app.route("/metapackages/not-in-repo/<repo>/<bound>")
def metapackages_not_in_repo(repo, bound=None):
    return metapackages_generic(bound, NotInRepoQueryFilter(repo))

@app.route("/metapackages/outdated-in-repo/<repo>/")
@app.route("/metapackages/outdated-in-repo/<repo>/<bound>")
def metapackages_outdated_in_repo(repo, bound=None):
    return metapackages_generic(bound, OutdatedInRepoQueryFilter(repo))

@app.route("/metapackages/by-maintainer/<maintainer>/")
@app.route("/metapackages/by-maintainer/<maintainer>/<bound>")
def metapackages_by_maintainer(maintainer, bound=None):
    return metapackages_generic(bound, MaintainerQueryFilter(maintainer))

@app.route("/metapackages/outdated-by-maintainer/<maintainer>/")
@app.route("/metapackages/outdated-by-maintainer/<maintainer>/<bound>")
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return metapackages_generic(bound, MaintainerOutdatedQueryFilter(maintainer))

@app.route("/maintainers/")
@app.route("/maintainers/<int:page>")
def maintainers(page=0):
    maintainers_count = database.GetMaintainersCount()
    maintainers = database.GetMaintainers(offset = page * PER_PAGE, limit = PER_PAGE)

    return flask.render_template(
        "maintainers.html",
        maintainers=maintainers,
        page=page,
        num_pages=((maintainers_count + PER_PAGE - 1) // PER_PAGE)
    )

@app.route("/metapackage/<name>")
def metapackage(name):
    packages = database.GetMetapackage(name)
    if not packages:
        flask.abort(404);

    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    repometadata = repoman.GetMetadata();
    return flask.render_template("package.html", packages=packages, repometadata=repometadata, name=name)

@app.route("/badge/all/<name>")
def badge_all(name):
    packageset = database.GetMetapackage(name)
    if not packageset:
        flask.abort(404);

    summaries = PackagesetToSummaries(packageset)
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
            "badge-big.svg",
            repositories=sorted(repostates, key=lambda repo: repo['name']),
            name=name
        ),
        {'Content-type': 'image/svg+xml'}
    )

@app.route("/badge/tiny/<name>")
def badge_tiny(name):
    packageset = database.GetMetapackage(name)
    if not packageset:
        flask.abort(404);

    summaries = PackagesetToSummaries(packageset)

    total_packages = 0
    newest_packages = 0
    for summary in summaries.values():
        total_packages += 1
        if summary['versionclass'] == RepositoryVersionClass.newest or summary['versionclass'] == RepositoryVersionClass.mixed:
            newest_packages += 1

    return (
        flask.render_template(
            "badge-small.svg",
            total_packages=total_packages,
            newest_packages=newest_packages,
            name=name
        ),
        {'Content-type': 'image/svg+xml'}
    )

@app.route("/news")
def news():
    return flask.render_template("news.html")

@app.route("/about")
def about():
    return flask.render_template("about.html")

@app.route("/api/v1/metapackage/<name>")
def api_v1_metapackage(name):
    return (
        json.dumps(list(map(
            api_v1_package_to_json,
            database.GetMetapackage(name)
        ))),
        {'Content-type': 'application/json'}
    )

@app.route("/api/v1/metapackages/all/")
@app.route("/api/v1/metapackages/all/<bound>")
def api_v1_metapackages_starting(bound=None):
    return (
        json.dumps(list(map(
            api_v1_package_to_json,
            database.GetMetapackages(
                NameStartingQueryFilter(bound),
                limit=PER_PAGE
            )
        ))),
        {'Content-type': 'application/json'}
    )

if __name__ == "__main__":
    app.run()
