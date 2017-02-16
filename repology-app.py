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
from repology.metapackageproc import *
from repology.package import *
from repology.packageproc import *
from repology.queryfilters import *
from repology.repoman import RepositoryManager
from repology.template_helpers import *
from repology.version import VersionCompare

# create application and handle configuration
app = flask.Flask(__name__)

app.config.from_pyfile('repology.conf.default')
app.config.from_pyfile('repology.conf', silent=True)
app.config.from_envvar('REPOLOGY_CONFIG', silent=True)

# global repology objects
repoman = RepositoryManager(app.config['REPOS_PATH'], "dummy")  # XXX: should not construct fetchers and parsers here
repometadata = repoman.GetMetadata()
reponames = repoman.GetNames(app.config['REPOSITORIES'])

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
app.jinja_env.globals['reponames'] = reponames


def get_db():
    if not hasattr(flask.g, 'database'):
        flask.g.database = Database(app.config['DSN'], readonly=True)
    return flask.g.database


# helpers
def api_v1_package_to_json(package):
    output = {
        field: getattr(package, field) for field in (
            'repo',
            'name',
            'version',
            'origversion',
            'maintainers',
            #'category',
            #'comment',
            #'homepage',
            'licenses',
            'downloads'
        ) if getattr(package, field)
    }

    # XXX: these tweaks should be implemented in core
    if package.homepage:
        output['www'] = [package.homepage]
    if package.comment:
        output['summary'] = package.comment
    if package.category:
        output['categories'] = [package.category]

    return output


def api_v1_metapackages_generic(bound, *filters):
    metapackages = PackagesToMetapackages(
        get_db().GetMetapackages(
            bound_to_filter(bound),
            *filters,
            limit=app.config['PER_PAGE']
        )
    )

    metapackages = {metapackage_name: list(map(api_v1_package_to_json, packageset)) for metapackage_name, packageset in metapackages.items()}

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


def metapackages_generic(bound, *filters, template='metapackages.html', repo=None, maintainer=None):
    namefilter = bound_to_filter(bound)

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

    metapackages = PackagesToMetapackages(packages)

    metapackagedata = {}
    for metapackagename, packages in sorted(metapackages.items()):
        packages = PackagesetSortByVersions(packages)

        # 1. Aggregate by repository
        packages_by_repo = {}
        for package in packages:
            if package.repo not in packages_by_repo:
                packages_by_repo[package.repo] = []
            packages_by_repo[package.repo].append(package)

        # 2.1. Extract explicit packages
        # 2.2. Discover repos worth showing
        # Repo not worth showin is the repo from which all newest (in this repo) packages
        # were extracted as explicit
        explicit_packages = []
        ignored_packages = []
        repos_worth_showing = set()
        for reponame, repopackages in packages_by_repo.items():
            bestversion = None
            for package in repopackages:
                # discover best version
                if bestversion is None and package.versionclass != PackageVersionClass.ignored:
                    bestversion = package.version

                if (repo is not None and repo == package.repo) or (maintainer is not None and maintainer in package.maintainers):
                    explicit_packages.append(package)
                elif package.versionclass == PackageVersionClass.ignored:
                    ignored_packages.append(package)
                elif VersionCompare(package.version, bestversion) == 0:
                    repos_worth_showing.add(reponame)

        # 3. Extract newest package from each repo
        newest_packages = []
        for reponame in repos_worth_showing:
            for package in packages_by_repo[reponame]:
                if package.versionclass != PackageVersionClass.ignored:
                    newest_packages.append(package)
                    break

        # 4. Aggregate by versions
        def VersionsDigest(version):
            return {
                'version': version['version'],
                'repos': set(map(lambda p: p.repo, version['packages'])),
                'class': version['packages'][0].versionclass,
            }

        versions = PackagesetAggregateByVersions(newest_packages)
        metapackagedata[metapackagename] = {
            'families': PackagesetToFamilies(packages),
            'explicit': map(VersionsDigest, PackagesetAggregateByVersions(explicit_packages)),
            'newest': map(VersionsDigest, filter(lambda v: v['packages'][0].versionclass == PackageVersionClass.newest, versions)),
            'outdated': map(VersionsDigest, filter(lambda v: v['packages'][0].versionclass == PackageVersionClass.outdated, versions)),
            'ignored': map(VersionsDigest, PackagesetAggregateByVersions(ignored_packages))
        }

    return flask.render_template(
        template,
        firstname=firstname,
        lastname=lastname,
        search=search,
        metapackagedata=metapackagedata,
        repo=repo,
        maintainer=maintainer
    )


@app.route("/")  # XXX: redirect to metapackages/all?
@app.route("/metapackages/")  # XXX: redirect to metapackages/all?
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
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        template="metapackages-in-repo.html",
        repo=repo,
    )


@app.route("/metapackages/outdated-in-repo/<repo>/")
@app.route("/metapackages/outdated-in-repo/<repo>/<bound>/")
def metapackages_outdated_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        OutdatedInRepoQueryFilter(repo),
        template="metapackages-outdated-in-repo.html",
        repo=repo,
    )


@app.route("/metapackages/not-in-repo/<repo>/")
@app.route("/metapackages/not-in-repo/<repo>/<bound>/")
def metapackages_not_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        NotInRepoQueryFilter(repo),
        template="metapackages-not-in-repo.html",
        repo=repo,
    )


@app.route("/metapackages/candidates-for-repo/<repo>/")
@app.route("/metapackages/candidates-for-repo/<repo>/<bound>/")
def metapackages_candidates_for_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        NotInRepoQueryFilter(repo),
        InNumFamiliesQueryFilter(more=5),
        template="metapackages-candidates-for-repo.html",
        repo=repo,
    )


@app.route("/metapackages/unique-in-repo/<repo>/")
@app.route("/metapackages/unique-in-repo/<repo>/<bound>/")
def metapackages_unique_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        InNumFamiliesQueryFilter(less=1),
        template="metapackages-unique-in-repo.html",
        repo=repo,
    )


@app.route("/metapackages/by-maintainer/<maintainer>/")
@app.route("/metapackages/by-maintainer/<maintainer>/<bound>/")
def metapackages_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerQueryFilter(maintainer),
        template="metapackages-by-maintainer.html",
        maintainer=maintainer,
    )


@app.route("/metapackages/outdated-by-maintainer/<maintainer>/")
@app.route("/metapackages/outdated-by-maintainer/<maintainer>/<bound>/")
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerOutdatedQueryFilter(maintainer),
        template="metapackages-outdated-by-maintainer.html",
        maintainer=maintainer,
    )


@app.route("/maintainers/")
@app.route("/maintainers/<page>/")
def maintainers(page=None):
    maintainers = get_db().GetMaintainersByLetter(page)  # handles page sanity inside

    return flask.render_template(
        "maintainers.html",
        maintainers=maintainers,
        page=page
    )


@app.route("/maintainer/<maintainer>")
def maintainer(maintainer):
    maintainer_info = get_db().GetMaintainerInformation(maintainer)
    metapackages = get_db().GetMaintainerMetapackages(maintainer, 500)
    similar_maintainers = get_db().GetMaintainerSimilarMaintainers(maintainer, 50)

    if not maintainer_info:
        flask.abort(404)

    return flask.render_template(
        "maintainer.html",
        maintainer=maintainer,
        maintainer_info=maintainer_info,
        metapackages=metapackages,
        similar_maintainers=similar_maintainers
    )


@app.route("/repositories/")
def repositories():
    return flask.render_template("repositories.html")


@app.route("/metapackage/<name>")
def metapackage(name):
    # metapackage landing page; just redirect to packages, may change in future
    return flask.redirect(flask.url_for('metapackage_versions', name=name), 303)


@app.route("/metapackage/<name>/versions")
def metapackage_versions(name):
    packages_by_repo = {}
    for package in get_db().GetMetapackage(name):
        if package.repo not in packages_by_repo:
            packages_by_repo[package.repo] = []
        packages_by_repo[package.repo].append(package)

    for repo, packages in packages_by_repo.items():
        packages_by_repo[repo] = PackagesetSortByVersions(packages)

    return flask.render_template("metapackage-versions.html", packages_by_repo=packages_by_repo, name=name)


@app.route("/metapackage/<name>/packages")
def metapackage_packages(name):
    packages = get_db().GetMetapackage(name)
    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    return flask.render_template(
        "metapackage-packages.html",
        packages=packages,
        name=name,
        link_statuses=get_db().GetMetapackageLinkStatuses(name)
    )


@app.route("/metapackage/<name>/information")
def metapackage_information(name):
    packages = get_db().GetMetapackage(name)
    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)

    information = {}

    def append_info(infokey, infoval, package):
        if infokey not in information:
            information[infokey] = {}

        if infoval not in information[infokey]:
            information[infokey][infoval] = set()

        information[infokey][infoval].add(package.family)

    for package in packages:
        append_info('names', package.name, package)
        append_info('versions', package.version, package)
        append_info('repos', package.repo, package)

        if package.comment:
            append_info('summaries', package.comment, package)
        for maintainer in package.maintainers:
            append_info('maintainers', maintainer, package)
        if package.category:
            append_info('categories', package.category, package)
        if package.homepage:
            append_info('homepages', package.homepage, package)
        for download in package.downloads:
            append_info('downloads', download, package)

    versions = PackagesetAggregateByVersions(packages)

    for version in versions:
        version['families'] = list(sorted(PackagesetToFamilies(version['packages'])))

    return flask.render_template(
        "metapackage-information.html",
        information=information,
        versions=versions,
        name=name,
        link_statuses=get_db().GetMetapackageLinkStatuses(name)
    )


@app.route("/metapackage/<name>/badges")
def metapackage_badges(name):
    packages = get_db().GetMetapackage(name)
    repos = sorted(list(set([package.repo for package in packages])))
    return flask.render_template("metapackage-badges.html", name=name, repos=repos)


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


@app.route("/badge/tiny-repos/<name>.svg")
def badge_tiny_repos(name):
    num_families = len(set([package.family for package in get_db().GetMetapackage(name)]))
    return (
        flask.render_template(
            "badge-tiny.svg",
            name=name,
            num_families=num_families
        ),
        {'Content-type': 'image/svg+xml'}
    )


@app.route("/badge/version-for-repo/<repo>/<name>.svg")
def badge_version_for_repo(repo, name):
    summaries = PackagesetToSummaries(get_db().GetMetapackage(name))
    if repo not in summaries:
        flask.abort(404)

    return (
        flask.render_template(
            "badge-tiny-version.svg",
            repo=repo,
            version=summaries[repo]['version'],
            versionclass=summaries[repo]['versionclass'],
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
        repostats=filter(lambda r: r['name'] in reponames, get_db().GetRepositories()),
        repostats_old={repo['name']: repo for repo in get_db().GetRepositoriesHistoryAgo(60 * 60 * 24 * 7)},
        num_metapackages=get_db().GetMetapackagesCount()
    )


@app.route("/graph/metapackages-for-repo/<repo>.svg")
def graph_metapackages_for_repo(repo):
    if repo not in reponames:
        flask.abort(404)

    numdays = 7
    period = 60 * 60 * 24 * numdays
    fields = ('num_metapackages', 'num_metapackages_unique', 'num_metapackages_newest', 'num_metapackages_outdated')

    history = get_db().GetRepositoriesHistoryPeriod(period)

    ranges = {}

    def update_ranges(name, value):
        if value is None:
            return
        if name not in ranges:
            ranges[name] = [value, value]
        if value < ranges[name][0]:
            ranges[name][0] = value
        if value > ranges[name][1]:
            ranges[name][1] = value

    def normalize_to_range(name, value):
        if name in ranges and ranges[name][0] != ranges[name][1]:
            return (value - ranges[name][0]) / (ranges[name][1] - ranges[name][0])
        return 0.5

    # collect min/max ranges for all fields
    for entry in history:
        entry['statistics'] = {repo['name']: repo for repo in entry['statistics']}

        if repo not in entry['statistics']:
            continue

        statistics = entry['statistics'][repo]

        for field in fields:
            update_ranges(field, statistics.get(field, None))
            update_ranges('all', statistics.get(field, None))

    datapoints = []
    for entry in history:
        datapoint = {
            'pos': entry['timedelta'].total_seconds() / period,
        }

        if repo not in entry['statistics']:
            continue

        statistics = entry['statistics'][repo]
        for field in fields:
            if field in statistics:
                datapoint[field] = normalize_to_range(field, statistics[field])

        datapoints.append(datapoint)

    return (
        flask.render_template(
            "graph-metapackages-for-repo.svg",
            datapoints=datapoints,
            numdays=numdays
        ),
        {'Content-type': 'image/svg+xml'}
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
    return api_v1_metapackages_generic(bound, NotInRepoQueryFilter(repo), InNumFamiliesQueryFilter(more=5))


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
