# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from collections import defaultdict
from datetime import timedelta
from functools import cmp_to_key

import flask

from libversion import version_compare

from repologyapp.afk import AFKChecker
from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.metapackages import packages_to_summary_items
from repologyapp.view_registry import ViewRegistrar

from repology.config import config
from repology.package import VersionClass
from repology.packageproc import PackagesetAggregateByVersion, PackagesetSortByVersion


@ViewRegistrar('/metapackage/<name>/versions')
def metapackage_versions(name):
    packages_by_repo = defaultdict(list)
    for package in get_db().get_metapackage_packages(name):
        packages_by_repo[package.repo].append(package)

    for repo, packages in packages_by_repo.items():
        packages_by_repo[repo] = PackagesetSortByVersion(packages)

    return flask.render_template(
        'metapackage-versions.html',
        reponames_absent=[reponame for reponame in repometadata.active_names() if reponame not in packages_by_repo],
        packages_by_repo=packages_by_repo,
        metapackage=get_db().get_metapackage(name),
        name=name
    )


@ViewRegistrar('/metapackage/<name>/packages')
def metapackage_packages(name):
    packages_by_repo = defaultdict(list)

    for package in get_db().get_metapackage_packages(name):
        packages_by_repo[package.repo].append(package)

    def _packageset_sort_by_name_version(packages):
        def compare(p1, p2):
            if p1.name < p2.name:
                return -1
            if p1.name > p2.name:
                return 1
            return p2.VersionCompare(p1)

        return sorted(packages, key=cmp_to_key(compare))

    packages = []
    for repo in repometadata.active_names():
        if repo in packages_by_repo:
            packages.extend(_packageset_sort_by_name_version(packages_by_repo[repo]))

    return flask.render_template(
        'metapackage-packages.html',
        packages=packages,
        metapackage=get_db().get_metapackage(name),
        name=name,
        link_statuses=get_db().get_metapackage_link_statuses(name)
    )


@ViewRegistrar('/metapackage/<name>/information')
def metapackage_information(name):
    packages = get_db().get_metapackage_packages(name)
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
        for license_ in package.licenses:
            append_info('licenses', license_, package)

    if 'repos' in information:
        # preserve repos order
        information['repos'] = [
            (reponame, information['repos'][reponame])
            for reponame in repometadata.active_names() if reponame in information['repos']
        ]

    versions = PackagesetAggregateByVersion(packages, {VersionClass.legacy: VersionClass.outdated})

    return flask.render_template(
        'metapackage-information.html',
        information=information,
        versions=versions,
        metapackage=get_db().get_metapackage(name),
        name=name,
        link_statuses=get_db().get_metapackage_link_statuses(name)
    )


@ViewRegistrar('/metapackage/<name>/history')
def metapackage_history(name):
    def prepare_repos(repos):
        if not repos:
            return []

        repos = set(repos)

        # ensure correct ordering
        return [name for name in repometadata.all_names() if name in repos]

    def prepare_versions(versions):
        if not versions:
            return []

        def version_compare_rev(v1, v2):
            return version_compare(v2, v1)

        return sorted(versions, key=cmp_to_key(version_compare_rev))

    def timedelta_from_seconds(seconds):
        return timedelta(seconds=seconds)

    def apply_to_field(datadict, key, func):
        if key in datadict and datadict[key] is not None:
            datadict[key] = func(datadict[key])

    def postprocess_history(history):
        for entry in history:
            data = entry['data']

            if entry['type'] == 'history_start':
                devel_repos = set(data.get('devel_repos', []))
                newest_repos = set(data.get('newest_repos', []))
                all_repos = set(data.get('all_repos', []))

                actual_repos = devel_repos | newest_repos
                old_repos = all_repos - actual_repos

                apply_to_field(data, 'devel_versions', prepare_versions)
                apply_to_field(data, 'newest_versions', prepare_versions)

                data['devel_repos'] = prepare_repos(devel_repos)
                data['newest_repos'] = prepare_repos(newest_repos)
                data['all_repos'] = prepare_repos(all_repos)

                data['actual_repos'] = prepare_repos(actual_repos)
                data['old_repos'] = prepare_repos(old_repos)

                yield entry

            elif entry['type'] == 'version_update':
                apply_to_field(data, 'versions', prepare_versions)
                apply_to_field(data, 'repos', prepare_repos)
                apply_to_field(data, 'passed', timedelta_from_seconds)
                yield entry

            elif entry['type'] == 'catch_up':
                apply_to_field(data, 'repos', prepare_repos)
                apply_to_field(data, 'lag', timedelta_from_seconds)

                if data['repos']:
                    yield entry

            elif entry['type'] == 'repos_update':
                apply_to_field(data, 'repos_added', prepare_repos)
                apply_to_field(data, 'repos_removed', prepare_repos)

                if data['repos_added'] or data['repos_removed']:
                    yield entry

            elif entry['type'] == 'history_end':
                apply_to_field(data, 'last_repos', prepare_repos)
                if data.get('last_repos'):
                    data['last_repo'] = data['last_repos'][0]

                yield entry

    return flask.render_template(
        'metapackage-history.html',
        metapackage=get_db().get_metapackage(name),
        name=name,
        history=list(postprocess_history(get_db().get_metapackage_history(name, limit=config['HISTORY_PER_PAGE'])))
    )


@ViewRegistrar('/metapackage/<name>/related')
def metapackage_related(name):
    metapackages = get_db().get_metapackage_related_metapackages(name, limit=config['METAPACKAGES_PER_PAGE'])

    packages = get_db().get_metapackages_packages(list(metapackages.keys()), fields=['family', 'effname', 'version', 'versionclass', 'flags'])

    metapackagedata = packages_to_summary_items(packages)

    too_many_warning = None
    if len(metapackagedata) == config['METAPACKAGES_PER_PAGE']:
        too_many_warning = config['METAPACKAGES_PER_PAGE']

    return flask.render_template(
        'metapackage-related.html',
        metapackage=get_db().get_metapackage(name),
        name=name,
        metapackages=metapackages,
        metapackagedata=metapackagedata,
        too_many_warning=too_many_warning
    )


@ViewRegistrar('/metapackage/<name>/badges')
def metapackage_badges(name):
    repos_present_in = set([package.repo for package in get_db().get_metapackage_packages(name)])
    repos = [repo for repo in repometadata.active_names() if repo in repos_present_in]
    return flask.render_template(
        'metapackage-badges.html',
        metapackage=get_db().get_metapackage(name),
        name=name,
        repos=repos
    )


@ViewRegistrar('/metapackage/<name>/report', methods=['GET', 'POST'])
def metapackage_report(name):
    reports_disabled = name in config['DISABLED_REPORTS']

    if flask.request.method == 'POST':
        if reports_disabled:
            flask.flash('Could not add report: new reports for this metapackage are disabled', 'warning')
            return flask.redirect(flask.url_for('metapackage_report', name=name))

        if get_db().get_metapackage_reports_count(name) >= config['MAX_REPORTS']:
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

        get_db().add_report(
            flask.request.remote_addr,
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
        reports=get_db().get_metapackage_reports(name),
        metapackage=get_db().get_metapackage(name),
        name=name,
        afk_till=AFKChecker(config['STAFF_AFK']).get_afk_end(),
        reports_disabled=reports_disabled,
        show_invitation=flask.request.remote_addr in config['INVITED_IPS']
    )
