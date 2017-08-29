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

import json
import math

from operator import itemgetter

import flask

from werkzeug.contrib.profiler import ProfilerMiddleware

from repology.database import Database
from repology.graphprocessor import GraphProcessor
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
repoman = RepositoryManager(app.config['REPOS_DIR'], 'dummy')  # XXX: should not construct fetchers and parsers here
repometadata = repoman.GetMetadata(app.config['REPOSITORIES'])
reponames = repoman.GetNames(app.config['REPOSITORIES'])

# templates: tuning
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# templates: custom filters
app.jinja_env.filters['pkg_format'] = pkg_format
app.jinja_env.filters['css_for_package_versionclass'] = css_for_package_versionclass
app.jinja_env.filters['css_for_summary_versionclass'] = css_for_summary_versionclass
app.jinja_env.filters['maintainer_to_links'] = maintainer_to_links
app.jinja_env.filters['maintainers_to_group_mailto'] = maintainers_to_group_mailto

# templates: custom tests
app.jinja_env.tests['for_page'] = for_page
app.jinja_env.tests['fallback_maintainer'] = is_fallback_maintainer

# templates: custom global functions
app.jinja_env.globals['url_for_self'] = url_for_self

# templates: custom global data
app.jinja_env.globals['REPOLOGY_HOME'] = app.config['REPOLOGY_HOME']
app.jinja_env.globals['repometadata'] = repometadata
app.jinja_env.globals['reponames'] = reponames


def get_db():
    if not hasattr(flask.g, 'database'):
        flask.g.database = Database(app.config['DSN'], readonly=False, autocommit=True)
    return flask.g.database


# helpers
def api_v1_package_to_json(package):
    output = {
        field: getattr(package, field) for field in (
            'repo',
            'subrepo',
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
            limit=app.config['METAPACKAGES_PER_PAGE']
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


def metapackages_to_data(metapackages, repo=None, maintainer=None):
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
                'families': set(map(lambda p: p.family, version['packages'])),
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

    return metapackagedata


def metapackages_generic(bound, *filters, template='metapackages.html', repo=None, maintainer=None):
    namefilter = bound_to_filter(bound)

    # process search
    search = flask.request.args.to_dict().get('search')
    searchfilter = NameSubstringQueryFilter(search) if search else None

    # get packages
    packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), searchfilter, *filters, limit=app.config['METAPACKAGES_PER_PAGE'])

    # on empty result, fallback to show first, last set of results
    if not packages:
        if bound and bound.startswith('<'):
            namefilter = NameStartingQueryFilter()
        else:
            namefilter = NameBeforeQueryFilter()
        packages = get_db().GetMetapackages(namefilter, InAnyRepoQueryFilter(reponames), searchfilter, *filters, limit=app.config['METAPACKAGES_PER_PAGE'])

    firstname, lastname = get_packages_name_range(packages)

    metapackagedata = metapackages_to_data(PackagesToMetapackages(packages), repo, maintainer)

    return flask.render_template(
        template,
        firstname=firstname,
        lastname=lastname,
        search=search,
        metapackagedata=metapackagedata,
        repo=repo,
        maintainer=maintainer
    )


@app.route('/')
def index():
    repostats = [
        repo for repo in get_db().GetRepositories()
        if repo['name'] in reponames and repometadata[repo['name']]['type'] == 'repository'
    ]

    top_repos = {
        'by_total': [
            {
                'name': repo['name'],
                'value': repo['num_metapackages'],
            }
            for repo in sorted(repostats, key=lambda repo: repo['num_metapackages'], reverse=True)[:10]
        ],
        'by_newest': [
            {
                'name': repo['name'],
                'value': repo['num_metapackages_newest'],
            }
            for repo in sorted(repostats, key=lambda repo: repo['num_metapackages_newest'], reverse=True)[:10]
        ],
        'by_pnewest': [
            {
                'name': repo['name'],
                'value': '{:.2f}%'.format(100.0 * repo['num_metapackages_newest'] / repo['num_metapackages'] if repo['num_metapackages'] else 0),
            }
            for repo in sorted(repostats, key=lambda repo: repo['num_metapackages_newest'] / (repo['num_metapackages'] or 1), reverse=True)[:10]
        ]
    }

    important_packages = [
        'apache24',
        'awesome',
        'bash',
        'binutils',
        'bison',
        'blender',
        'boost',
        'bzip2',
        'chromium',
        'claws-mail',
        'cmake',
        'cppcheck',
        'cups',
        'curl',
        'darktable',
        'dia',
        'djvulibre',
        'dosbox',
        'dovecot',
        'doxygen',
        'dvd+rw-tools',
        'emacs',
        'exim',
        'ffmpeg',
        'firefox',
        'flex',
        'fluxbox',
        'freecad',
        'freetype',
        'gcc',
        'gdb',
        'geeqie',
        'gimp',
        'git',
        'gnupg',
        'go',
        'graphviz',
        'grub',
        'icewm',
        'imagemagick',
        'inkscape',
        'irssi',
        'kodi',
        'lame',
        'lftp',
        'libreoffice',
        'libressl',
        'lighttpd',
        'links',
        'llvm',
        'mariadb',
        'maxima',
        'mc',
        'memcached',
        'mercurial',
        'mesa',
        'mplayer',
        'mutt',
        'mysql',
        'nginx',
        'nmap',
        'octave',
        'openbox',
        'openssh',
        'openssl',
        'openttf',
        'openvpn',
        'p7zip',
        'perl',
        'pidgin',
        'postfix',
        'postgresql',
        'privoxy',
        'procmail',
        'python3',
        'qemu',
        'rdesktop',
        'redis',
        'rrdtool',
        'rsync',
        'rtorrent',
        'rxvt-unicode',
        'samba',
        'sane-backends',
        'scons',
        'screen',
        'scribus',
        'scummvm',
        'sdl2',
        'smartmontools',
        'sqlite3',
        'squid',
        'subversion',
        'sudo',
        'sumversion',
        'thunderbird',
        'tigervnc',
        'tmux',
        'tor',
        'valgrind',
        'vim',
        'virtualbox',
        'vlc',
        'vsftpd',
        'wayland',
        'wesnoth',
        'wget',
        'wine',
        'wireshark',
        'xorg-server',
        'youtube-dl',
        'zsh',
    ]

    packages = get_db().GetMetapackage(important_packages)

    metapackagedata = metapackages_to_data(PackagesToMetapackages(packages))

    return flask.render_template(
        'index.html',
        top_repos=top_repos,
        metapackagedata=metapackagedata
    )


@app.route('/metapackages/')  # XXX: redirect to metapackages/all?
@app.route('/metapackages/all/')
@app.route('/metapackages/all/<bound>/')
def metapackages_all(bound=None):
    return metapackages_generic(
        bound,
        template='metapackages-all.html'
    )


@app.route('/metapackages/unique/')
@app.route('/metapackages/unique/<bound>/')
def metapackages_unique(bound=None):
    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(less=1),
        template='metapackages-unique.html'
    )


@app.route('/metapackages/widespread/')
@app.route('/metapackages/widespread/<bound>/')
def metapackages_widespread(bound=None):
    return metapackages_generic(
        bound,
        InNumFamiliesQueryFilter(more=10),
        template='metapackages-widespread.html'
    )


@app.route('/metapackages/in-repo/<repo>/')
@app.route('/metapackages/in-repo/<repo>/<bound>/')
def metapackages_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        InRepoQueryFilter(repo),
        template='metapackages-in-repo.html',
        repo=repo,
    )


@app.route('/metapackages/outdated-in-repo/<repo>/')
@app.route('/metapackages/outdated-in-repo/<repo>/<bound>/')
def metapackages_outdated_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        OutdatedInRepoQueryFilter(repo),
        template='metapackages-outdated-in-repo.html',
        repo=repo,
    )


@app.route('/metapackages/not-in-repo/<repo>/')
@app.route('/metapackages/not-in-repo/<repo>/<bound>/')
def metapackages_not_in_repo(repo, bound=None):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return metapackages_generic(
        bound,
        NotInRepoQueryFilter(repo),
        template='metapackages-not-in-repo.html',
        repo=repo,
    )


@app.route('/metapackages/candidates-for-repo/<repo>/')
@app.route('/metapackages/candidates-for-repo/<repo>/<bound>/')
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


@app.route('/metapackages/unique-in-repo/<repo>/')
@app.route('/metapackages/unique-in-repo/<repo>/<bound>/')
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


@app.route('/metapackages/by-maintainer/<maintainer>/')
@app.route('/metapackages/by-maintainer/<maintainer>/<bound>/')
def metapackages_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerQueryFilter(maintainer),
        template='metapackages-by-maintainer.html',
        maintainer=maintainer,
    )


@app.route('/metapackages/outdated-by-maintainer/<maintainer>/')
@app.route('/metapackages/outdated-by-maintainer/<maintainer>/<bound>/')
def metapackages_outdated_by_maintainer(maintainer, bound=None):
    return metapackages_generic(
        bound,
        MaintainerOutdatedQueryFilter(maintainer),
        template='metapackages-outdated-by-maintainer.html',
        maintainer=maintainer,
    )


@app.route('/maintainers/')
@app.route('/maintainers/<bound>/')
def maintainers(bound=None):
    reverse = False
    if bound and bound.startswith('..'):
        bound = bound[2:]
        reverse = True
    elif bound and bound.endswith('..'):
        bound = bound[:-2]

    search = flask.request.args.to_dict().get('search')

    minmaintainer, maxmaintainer = get_db().GetMaintainersRange()

    maintainers = get_db().GetMaintainers(bound, reverse, search, app.config['MAINTAINERS_PER_PAGE'])

    firstpage, lastpage = False, False
    for maintainer in maintainers:
        if maintainer['maintainer'] == minmaintainer:
            firstpage = True
        if maintainer['maintainer'] == maxmaintainer:
            lastpage = True

    return flask.render_template(
        'maintainers.html',
        search=search,
        minmaintainer=minmaintainer,
        maxmaintainer=maxmaintainer,
        firstpage=firstpage,
        lastpage=lastpage,
        maintainers=maintainers
    )


@app.route('/maintainer/<maintainer>')
def maintainer(maintainer):
    maintainer_info = get_db().GetMaintainerInformation(maintainer)
    metapackages = get_db().GetMaintainerMetapackages(maintainer, 500)
    similar_maintainers = get_db().GetMaintainerSimilarMaintainers(maintainer, 50)
    numproblems = get_db().GetProblemsCount(maintainer=maintainer)

    if not maintainer_info:
        flask.abort(404)

    return flask.render_template(
        'maintainer.html',
        numproblems=numproblems,
        maintainer=maintainer,
        maintainer_info=maintainer_info,
        metapackages=metapackages,
        similar_maintainers=similar_maintainers
    )


@app.route('/maintainer/<maintainer>/problems')
def maintainer_problems(maintainer):
    return flask.render_template(
        'maintainer-problems.html',
        maintainer=maintainer,
        problems=get_db().GetProblems(
            maintainer=maintainer,
            limit=app.config['PROBLEMS_PER_PAGE']
        )
    )


@app.route('/repositories/')
def repositories():
    return flask.render_template('repositories.html')


@app.route('/repository/<repo>')
def repository(repo):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.render_template(
        'repository.html',
        repo=repo,
        repo_info=get_db().GetRepository(repo)
    )


@app.route('/repository/<repo>/problems')
def repository_problems(repo):
    if not repo or repo not in repometadata:
        flask.abort(404)

    return flask.render_template('repository-problems.html', repo=repo, problems=get_db().GetProblems(repo=repo, limit=app.config['PROBLEMS_PER_PAGE']))


@app.route('/metapackage/<name>')
def metapackage(name):
    # metapackage landing page; just redirect to packages, may change in future
    return flask.redirect(flask.url_for('metapackage_versions', name=name), 303)


@app.route('/metapackage/<name>/versions')
def metapackage_versions(name):
    packages_by_repo = {}
    for package in get_db().GetMetapackage(name):
        if package.repo not in packages_by_repo:
            packages_by_repo[package.repo] = []
        packages_by_repo[package.repo].append(package)

    for repo, packages in packages_by_repo.items():
        packages_by_repo[repo] = PackagesetSortByVersions(packages)

    return flask.render_template(
        'metapackage-versions.html',
        reponames_absent=[reponame for reponame in reponames if reponame not in packages_by_repo],
        packages_by_repo=packages_by_repo,
        name=name
    )


@app.route('/metapackage/<name>/packages')
def metapackage_packages(name):
    packages = get_db().GetMetapackage(name)
    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    return flask.render_template(
        'metapackage-packages.html',
        packages=packages,
        name=name,
        link_statuses=get_db().GetMetapackageLinkStatuses(name)
    )


@app.route('/metapackage/<name>/information')
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
        'metapackage-information.html',
        information=information,
        versions=versions,
        name=name,
        link_statuses=get_db().GetMetapackageLinkStatuses(name)
    )


@app.route('/metapackage/<name>/related')
def metapackage_related(name):
    names = get_db().GetRelatedMetapackages(name, limit=app.config['METAPACKAGES_PER_PAGE'])

    too_many_warning = None
    if len(names) == app.config['METAPACKAGES_PER_PAGE']:
        too_many_warning = app.config['METAPACKAGES_PER_PAGE']

    packages = get_db().GetMetapackage(names)

    metapackagedata = metapackages_to_data(PackagesToMetapackages(packages))

    return flask.render_template(
        'metapackage-related.html',
        name=name,
        metapackagedata=metapackagedata,
        too_many_warning=too_many_warning
    )


@app.route('/metapackage/<name>/badges')
def metapackage_badges(name):
    packages = get_db().GetMetapackage(name)
    repos = sorted(list(set([package.repo for package in packages])))
    return flask.render_template('metapackage-badges.html', name=name, repos=repos)


@app.route('/metapackage/<name>/report', methods=['GET', 'POST'])
def metapackage_report(name):
    if flask.request.method == 'POST':
        if get_db().GetReportsCount(name) >= app.config['MAX_REPORTS']:
            flask.flash('Could not add report: too many reports for this metapackage', 'danger')
            return flask.redirect(flask.url_for('metapackage_report', name=name))

        need_verignore = 'need_verignore' in flask.request.form
        need_split = 'need_split' in flask.request.form
        need_merge = 'need_merge' in flask.request.form
        comment = flask.request.form.get('comment', '').strip().replace('\r', '') or None

        if comment and len(comment) > 1024:
            flask.flash('Could not add report: comment os too long', 'danger')
            return flask.redirect(flask.url_for('metapackage_report', name=name))

        if not need_verignore and not need_split and not need_merge and not comment:
            flask.flash('Could not add report: please fill out the form', 'danger')
            return flask.redirect(flask.url_for('metapackage_report', name=name))

        if '<a href' in comment:
            flask.flash('Spammers not welcome, HTML not allowed', 'danger')
            return flask.redirect(flask.url_for('metapackage_report', name=name))

        get_db().AddReport(
            name,
            need_verignore,
            need_split,
            need_merge,
            comment
        )

        flask.flash('Report for {} added succesfully and will be processed in a few days, thank you!'.format(name), 'success')
        return flask.redirect(flask.url_for('metapackage_report', name=name))

    return flask.render_template(
        'metapackage-report.html',
        reports=get_db().GetReports(name),
        name=name,
        afk_till=AFKChecker(app.config['STAFF_AFK']).GetAFKEnd()
    )


@app.route('/badge/vertical-allrepos/<name>.svg')
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
            'badge-vertical.svg',
            repositories=sorted(repostates, key=lambda repo: repo['name']),
            name=name
        ),
        {'Content-type': 'image/svg+xml'}
    )


@app.route('/badge/tiny-repos/<name>.svg')
def badge_tiny_repos(name):
    num_families = len(set([package.family for package in get_db().GetMetapackage(name)]))
    return (
        flask.render_template(
            'badge-tiny.svg',
            name=name,
            num_families=num_families
        ),
        {'Content-type': 'image/svg+xml'}
    )


@app.route('/badge/version-for-repo/<repo>/<name>.svg')
def badge_version_for_repo(repo, name):
    summaries = PackagesetToSummaries(get_db().GetMetapackage(name))
    if repo not in summaries:
        flask.abort(404)

    return (
        flask.render_template(
            'badge-tiny-version.svg',
            repo=repo,
            version=summaries[repo]['version'],
            versionclass=summaries[repo]['versionclass'],
        ),
        {'Content-type': 'image/svg+xml'}
    )


@app.route('/news')
def news():
    return flask.render_template('news.html')


@app.route('/about')
def about():
    return flask.render_template('about.html')


@app.route('/opensearch/metapackage.xml')
def opensearch_metapackage():
    return flask.render_template('opensearch-metapackage.xml'), {'Content-type': 'application/xml'}


@app.route('/opensearch/maintainer.xml')
def opensearch_maintainer():
    return flask.render_template('opensearch-maintainer.xml'), {'Content-type': 'application/xml'}


@app.route('/statistics')
@app.route('/statistics/<sorting>')
def statistics(sorting=None):
    repostats = filter(lambda r: r['name'] in reponames, get_db().GetRepositories())
    showmedals = True

    if sorting == 'newest':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_newest'], reverse=True)
    elif sorting == 'pnewest':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_newest'] / (s['num_metapackages'] or 1), reverse=True)
    elif sorting == 'outdated':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_outdated'], reverse=True)
    elif sorting == 'poutdated':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages_outdated'] / (s['num_metapackages'] or 1), reverse=True)
    elif sorting == 'total':
        repostats = sorted(repostats, key=lambda s: s['num_metapackages'], reverse=True)
    else:
        sorting = 'name'
        repostats = sorted(repostats, key=lambda s: s['name'])
        showmedals = False

    return flask.render_template(
        'statistics.html',
        sorting=sorting,
        repostats=repostats,
        showmedals=showmedals,
        repostats_old={},  # {repo['name']: repo for repo in get_db().GetRepositoriesHistoryAgo(60 * 60 * 24 * 7)},
        num_metapackages=get_db().GetMetapackagesCount()
    )


def graph_generic(getgraph, color, suffix=''):
    # use autoscaling until history is filled
    numdays = 14
    width = 1140
    height = 400
    gwidth = width - 50
    gheight = height - 20
    period = 60 * 60 * 24 * numdays

    graph = getgraph(period)

    return (
        flask.render_template(
            'graph.svg',
            width=width,
            height=height,
            gwidth=gwidth,
            gheight=gheight,
            points=graph.GetPoints(period),
            yticks=graph.GetYTicks(suffix),
            color=color,
            numdays=numdays,
            x=lambda x: int((1.0 - x) * gwidth) + 0.5,
            y=lambda y: int(10.0 + (1.0 - y) * (gheight - 20.0)) + 0.5,
        ),
        {'Content-type': 'image/svg+xml'}
    )


def graph_repo_generic(repo, getvalue, color, suffix=''):
    if repo not in reponames:
        flask.abort(404)

    def GetGraph(period):
        graph = GraphProcessor()

        for histentry in get_db().GetRepositoriesHistoryPeriod(period, repo):
            try:
                graph.AddPoint(histentry['timedelta'], getvalue(histentry['snapshot']))
            except:
                pass  # ignore missing keys, division errors etc.

        return graph

    return graph_generic(GetGraph, color, suffix)


def graph_total_generic(getvalue, color, suffix=''):
    def GetGraph(period):
        graph = GraphProcessor()

        for histentry in get_db().GetStatisticsHistoryPeriod(period):
            try:
                graph.AddPoint(histentry['timedelta'], getvalue(histentry['snapshot']))
            except:
                pass  # ignore missing keys, division errors etc.

        return graph

    return graph_generic(GetGraph, color, suffix)


@app.route('/graph/repo/<repo>/metapackages_total.svg')
def graph_repo_metapackages_total(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages'], '#000000')


@app.route('/graph/repo/<repo>/metapackages_newest.svg')
def graph_repo_metapackages_newest(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_newest'], '#5cb85c')


@app.route('/graph/repo/<repo>/metapackages_newest_percent.svg')
def graph_repo_metapackages_newest_percent(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_newest'] / s['num_metapackages'] * 100.0, '#5cb85c', '%')


@app.route('/graph/repo/<repo>/metapackages_outdated.svg')
def graph_repo_metapackages_outdated(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_outdated'], '#d9534f')


@app.route('/graph/repo/<repo>/metapackages_outdated_percent.svg')
def graph_repo_metapackages_outdated_percent(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_outdated'] / s['num_metapackages'] * 100.0, '#d9534f', '%')


@app.route('/graph/repo/<repo>/metapackages_unique.svg')
def graph_repo_metapackages_unique(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_unique'], '#5bc0de')


@app.route('/graph/repo/<repo>/metapackages_unique_percent.svg')
def graph_repo_metapackages_unique_percent(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_unique'] / s['num_metapackages'] * 100.0, '#5bc0de', '%')


@app.route('/graph/repo/<repo>/problems.svg')
def graph_repo_problems(repo):
    return graph_repo_generic(repo, lambda s: s['num_problems'], '#c00000')


@app.route('/graph/repo/<repo>/problems_per_metapackage.svg')
def graph_repo_problems_per_metapackage(repo):
    return graph_repo_generic(repo, lambda s: s['num_problems'] / s['num_metapackages'], '#c00000')


@app.route('/graph/repo/<repo>/maintainers.svg')
def graph_repo_maintainers(repo):
    return graph_repo_generic(repo, lambda s: s['num_maintainers'], '#c000c0')


@app.route('/graph/repo/<repo>/packages_per_maintainer.svg')
def graph_repo_packages_per_maintainer(repo):
    return graph_repo_generic(repo, lambda s: s['num_packages'] / s['num_maintainers'], '#c000c0')


@app.route('/graph/total/packages.svg')
def graph_total_packages():
    return graph_total_generic(lambda s: s['num_packages'], '#000000')


@app.route('/graph/total/metapackages.svg')
def graph_total_metapackages():
    return graph_total_generic(lambda s: s['num_metapackages'], '#000000')


@app.route('/graph/total/maintainers.svg')
def graph_total_maintainers():
    return graph_total_generic(lambda s: s['num_maintainers'], '#c000c0')


@app.route('/graph/total/problems.svg')
def graph_total_problems():
    return graph_total_generic(lambda s: s['num_problems'], '#c00000')


def clever_ceil(value):
    if value == 0:
        return 1

    tick = math.pow(10, math.ceil(math.log(value, 10) - 2))
    return int(math.ceil(value / tick) * tick)


def map_repo_generic(repo2coords, namex='X', namey='Y', unitx='', unity=''):
    snapshots = [
        #get_db().GetRepositoriesHistoryAgo(60 * 60 * 24 * 30)
    ]

    points = []
    for repo in get_db().GetRepositories():
        if not repo['name'] in reponames:
            continue

        point = {
            'text': repometadata[repo['name']]['desc'],
            'coords': list(map(repo2coords, [repo] + [snapshot[repo['name']] for snapshot in snapshots if repo['name'] in snapshot]))
        }

        if 'color' in repometadata[repo['name']]:
            point['color'] = repometadata[repo['name']]['color']

        points.append(point)

    width = 1140
    height = 800

    return (
        flask.render_template(
            'map.svg',
            width=width,
            height=height,
            minx=0,
            miny=0,
            maxx=clever_ceil(max(map(lambda p: p['coords'][0]['x'], points))),
            maxy=clever_ceil(max(map(lambda p: p['coords'][0]['y'], points))),
            namex=namex,
            namey=namey,
            unitx=unitx,
            unity=unity,
            points=points,
        ),
        {'Content-type': 'image/svg+xml'}
    )


@app.route('/graph/map_repo_size_fresh.svg')
def graph_map_repo_size_fresh():
    def repo2coords(repo):
        return {
            'x': repo['num_metapackages'],
            'y': repo['num_metapackages_newest']
        }

    return map_repo_generic(
        repo2coords,
        namex='Number of packages in repository',
        namey='Number of fresh packages in repository'
    )


@app.route('/graph/map_repo_size_freshness.svg')
def graph_map_repo_size_freshness():
    def repo2coords(repo):
        return {
            'x': repo['num_metapackages'],
            'y': 100.0 * repo['num_metapackages_newest'] / repo['num_metapackages'] if repo['num_metapackages'] else 0
        }

    return map_repo_generic(
        repo2coords,
        namex='Number of packages in repository',
        namey='Percentage of fresh packages',
        unity='%'
    )


@app.route('/api/v1/metapackage/<name>')
def api_v1_metapackage(name):
    return (
        json.dumps(list(map(
            api_v1_package_to_json,
            get_db().GetMetapackage(name)
        ))),
        {'Content-type': 'application/json'}
    )


@app.route('/api')
@app.route('/api/v1')
def api_v1():
    return flask.render_template('api.html', per_page=app.config['METAPACKAGES_PER_PAGE'])


@app.route('/api/v1/metapackages/')
@app.route('/api/v1/metapackages/all/')
@app.route('/api/v1/metapackages/all/<bound>/')
def api_v1_metapackages_all(bound=None):
    return api_v1_metapackages_generic(bound)


@app.route('/api/v1/metapackages/unique/')
@app.route('/api/v1/metapackages/unique/<bound>/')
def api_v1_metapackages_unique(bound=None):
    return api_v1_metapackages_generic(bound, InNumFamiliesQueryFilter(less=1))


@app.route('/api/v1/metapackages/in-repo/<repo>/')
@app.route('/api/v1/metapackages/in-repo/<repo>/<bound>/')
def api_v1_metapackages_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, InRepoQueryFilter(repo))


@app.route('/api/v1/metapackages/outdated-in-repo/<repo>/')
@app.route('/api/v1/metapackages/outdated-in-repo/<repo>/<bound>/')
def api_v1_metapackages_outdated_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, OutdatedInRepoQueryFilter(repo))


@app.route('/api/v1/metapackages/not-in-repo/<repo>/')
@app.route('/api/v1/metapackages/not-in-repo/<repo>/<bound>/')
def api_v1_metapackages_not_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, NotInRepoQueryFilter(repo))


@app.route('/api/v1/metapackages/candidates-in-repo/<repo>/')
@app.route('/api/v1/metapackages/candidates-in-repo/<repo>/<bound>/')
def api_v1_metapackages_candidates_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, NotInRepoQueryFilter(repo), InNumFamiliesQueryFilter(more=5))


@app.route('/api/v1/metapackages/unique-in-repo/<repo>/')
@app.route('/api/v1/metapackages/unique-in-repo/<repo>/<bound>/')
def api_v1_metapackages_unique_in_repo(repo, bound=None):
    return api_v1_metapackages_generic(bound, InNumFamiliesQueryFilter(less=1))


@app.route('/api/v1/metapackages/by-maintainer/<maintainer>/')
@app.route('/api/v1/metapackages/by-maintainer/<maintainer>/<bound>/')
def api_v1_metapackages_by_maintainer(maintainer, bound=None):
    return api_v1_metapackages_generic(bound, MaintainerQueryFilter(maintainer))


@app.route('/api/v1/metapackages/outdated-by-maintainer/<maintainer>/')
@app.route('/api/v1/metapackages/outdated-by-maintainer/<maintainer>/<bound>/')
def api_v1_metapackages_outdated_by_maintainer(maintainer, bound=None):
    return api_v1_metapackages_generic(bound, MaintainerOutdatedQueryFilter(maintainer))


@app.route('/api/v1/repository/<repo>/problems')
def api_v1_repository_problems(repo):
    return (
        json.dumps(get_db().GetProblems(repo=repo)),
        {'Content-type': 'application/json'}
    )


@app.route('/api/v1/maintainer/<maintainer>/problems')
def api_v1_maintainer_problems(maintainer):
    return (
        json.dumps(get_db().GetProblems(maintainer=maintainer)),
        {'Content-type': 'application/json'}
    )


if __name__ == '__main__':
    if app.config['PROFILE']:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        app.run(debug=True)
    else:
        app.run()
