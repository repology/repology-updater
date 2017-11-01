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
from repologyapp.metapackages import metapackages_to_summary_items
from repologyapp.template_helpers import AFKChecker
from repologyapp.view_registry import ViewRegistrar

from repology.config import config
from repology.metapackageproc import PackagesToMetapackages
from repology.package import VersionClass
from repology.packageproc import PackagesetAggregateByVersions, PackagesetSortByNameVersion, PackagesetSortByVersions, PackagesetToFamilies


@ViewRegistrar('/metapackage/<name>')
def metapackage(name):
    # metapackage landing page; just redirect to packages, may change in future
    return flask.redirect(flask.url_for('metapackage_versions', name=name), 303)


@ViewRegistrar('/metapackage/<name>/versions')
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


@ViewRegistrar('/metapackage/<name>/packages')
def metapackage_packages(name):
    packages_by_repo = {}

    for package in get_db().GetMetapackage(name):
        packages_by_repo.setdefault(package.repo, []).append(package)

    packages = []
    for repo in reponames:
        if repo in packages_by_repo:
            packages.extend(PackagesetSortByNameVersion(packages_by_repo[repo]))

    return flask.render_template(
        'metapackage-packages.html',
        packages=packages,
        name=name,
        link_statuses=get_db().GetMetapackageLinkStatuses(name)
    )


@ViewRegistrar('/metapackage/<name>/information')
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

    if 'repos' in information:
        # preserve repos order
        information['repos'] = [
            (reponame, information['repos'][reponame])
            for reponame in reponames if reponame in information['repos']
        ]

    versions = PackagesetAggregateByVersions(packages, {VersionClass.legacy: VersionClass.outdated})

    for version in versions:
        version['families'] = list(sorted(PackagesetToFamilies(version['packages'])))

    return flask.render_template(
        'metapackage-information.html',
        information=information,
        versions=versions,
        name=name,
        link_statuses=get_db().GetMetapackageLinkStatuses(name)
    )


@ViewRegistrar('/metapackage/<name>/related')
def metapackage_related(name):
    packages = get_db().GetRelatedMetapackages(name, limit=config['METAPACKAGES_PER_PAGE'])

    metapackagedata = metapackages_to_summary_items(PackagesToMetapackages(packages))

    too_many_warning = None
    if len(metapackagedata) == config['METAPACKAGES_PER_PAGE']:
        too_many_warning = config['METAPACKAGES_PER_PAGE']

    return flask.render_template(
        'metapackage-related.html',
        name=name,
        metapackagedata=metapackagedata,
        too_many_warning=too_many_warning
    )


@ViewRegistrar('/metapackage/<name>/badges')
def metapackage_badges(name):
    repos_present_in = set([package.repo for package in get_db().GetMetapackage(name)])
    repos = [repo for repo in reponames if repo in repos_present_in]
    return flask.render_template('metapackage-badges.html', name=name, repos=repos)


@ViewRegistrar('/metapackage/<name>/report', methods=['GET', 'POST'])
def metapackage_report(name):
    if flask.request.method == 'POST':
        if get_db().GetReportsCount(name) >= config['MAX_REPORTS']:
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

        if comment and '<a href' in comment:
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
        afk_till=AFKChecker(config['STAFF_AFK']).GetAFKEnd()
    )
