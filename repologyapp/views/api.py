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

import flask

from repologyapp.config import config
from repologyapp.db import get_db
from repologyapp.metapackages import MetapackagesFilterInfo, packages_to_metapackages
from repologyapp.view_registry import ViewRegistrar

from repology.package import VersionClass


def api_v1_package_to_json(package):
    output = {
        field: getattr(package, field) for field in (
            'repo',
            'subrepo',
            'name',
            'version',
            #'origversion',
            #'status',
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

    output['status'] = VersionClass.ToString(package.versionclass)
    output['origversion'] = package.rawversion if package.rawversion != package.version else None

    return output


def dump_json(data):
    if config['PRETTY_JSON']:
        return json.dumps(data, indent=1, sort_keys=True)
    else:
        return json.dumps(data, separators=(',', ':'))


@ViewRegistrar('/api/v1/metapackages/')
@ViewRegistrar('/api/v1/metapackages/<bound>/')
def api_v1_metapackages(bound=None):
    filterinfo = MetapackagesFilterInfo()
    filterinfo.ParseFlaskArgs()

    request = filterinfo.GetRequest()
    request.Bound(bound)

    metapackages = get_db().query_metapackages(**request.__dict__, limit=config['METAPACKAGES_PER_PAGE'])

    packages = get_db().get_metapackages_packages(list(metapackages.keys()))

    metapackages = packages_to_metapackages(packages)

    metapackages = {
        metapackage_name: [api_v1_package_to_json(package) for package in packageset]
        for metapackage_name, packageset in metapackages.items()
    }

    return (
        dump_json(metapackages),
        {'Content-type': 'application/json'}
    )


@ViewRegistrar('/api')
@ViewRegistrar('/api/v1')
def api_v1():
    return flask.render_template('api.html', per_page=config['METAPACKAGES_PER_PAGE'])


@ViewRegistrar('/api/v1/metapackage/<name>')
def api_v1_metapackage(name):
    return (
        dump_json(list(map(
            api_v1_package_to_json,
            get_db().get_metapackage_packages(name)
        ))),
        {'Content-type': 'application/json'}
    )


@ViewRegistrar('/api/v1/metapackages/all/')
@ViewRegistrar('/api/v1/metapackages/all/<bound>/')
def api_v1_metapackages_all(bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound), 301)


@ViewRegistrar('/api/v1/metapackages/unique/')
@ViewRegistrar('/api/v1/metapackages/unique/<bound>/')
def api_v1_metapackages_unique(bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, families=1), 301)


@ViewRegistrar('/api/v1/metapackages/in-repo/<repo>/')
@ViewRegistrar('/api/v1/metapackages/in-repo/<repo>/<bound>/')
def api_v1_metapackages_in_repo(repo, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, inrepo=repo), 301)


@ViewRegistrar('/api/v1/metapackages/outdated-in-repo/<repo>/')
@ViewRegistrar('/api/v1/metapackages/outdated-in-repo/<repo>/<bound>/')
def api_v1_metapackages_outdated_in_repo(repo, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, inrepo=repo, outdated=1), 301)


@ViewRegistrar('/api/v1/metapackages/not-in-repo/<repo>/')
@ViewRegistrar('/api/v1/metapackages/not-in-repo/<repo>/<bound>/')
def api_v1_metapackages_not_in_repo(repo, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, notinrepo=repo), 301)


@ViewRegistrar('/api/v1/metapackages/candidates-in-repo/<repo>/')
@ViewRegistrar('/api/v1/metapackages/candidates-in-repo/<repo>/<bound>/')
def api_v1_metapackages_candidates_in_repo(repo, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, inrepo=repo, families='5-'), 301)


@ViewRegistrar('/api/v1/metapackages/unique-in-repo/<repo>/')
@ViewRegistrar('/api/v1/metapackages/unique-in-repo/<repo>/<bound>/')
def api_v1_metapackages_unique_in_repo(repo, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, inrepo=repo, families=1), 301)


@ViewRegistrar('/api/v1/metapackages/by-maintainer/<maintainer>/')
@ViewRegistrar('/api/v1/metapackages/by-maintainer/<maintainer>/<bound>/')
def api_v1_metapackages_by_maintainer(maintainer, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, maintainer=maintainer), 301)


@ViewRegistrar('/api/v1/metapackages/outdated-by-maintainer/<maintainer>/')
@ViewRegistrar('/api/v1/metapackages/outdated-by-maintainer/<maintainer>/<bound>/')
def api_v1_metapackages_outdated_by_maintainer(maintainer, bound=None):
    return flask.redirect(flask.url_for('api_v1_metapackages', bound=bound, maintainer=maintainer, outdated=1), 301)


@ViewRegistrar('/api/v1/repository/<repo>/problems')
def api_v1_repository_problems(repo):
    return (
        dump_json(get_db().get_repository_problems(repo)),
        {'Content-type': 'application/json'}
    )


@ViewRegistrar('/api/v1/maintainer/<maintainer>/problems')
def api_v1_maintainer_problems(maintainer):
    return (
        dump_json(get_db().get_maintainer_problems(maintainer)),
        {'Content-type': 'application/json'}
    )


@ViewRegistrar('/api/experimental/distromap')
def api_experimental_distromap():
    args = flask.request.args.to_dict()

    expand = bool(args.get('expand'))
    plaintext = args.get('format') == 'plaintext'

    distromap = None

    if expand:
        distromap = get_db().get_distromap_expanded(args.get('fromrepo'), args.get('torepo'))

        if plaintext:
            lines = ['\t'.join(pair) for pair in distromap]
            text = '\n'.join(lines + [''])
            return (text, {'Content-type': 'text/plain'})
    else:
        distromap = get_db().get_distromap(args.get('fromrepo'), args.get('torepo'))

        if plaintext:
            lines = [','.join(fromnames) + '\t' + ','.join(tonames) for fromnames, tonames in distromap]
            text = '\n'.join(lines + [''])
            return (text, {'Content-type': 'text/plain'})

    return (dump_json(distromap), {'Content-type': 'application/json'})


#@ViewRegistrar('/api/v1/history/repository/<repo>')
#def api_v1_maintainer_problems():
#    get_db().GetRepositoriesHistoryPeriod(seconds = 365
#    return (
#        dump_json(get_db().GetProblems(maintainer=maintainer)),
#        {'Content-type': 'application/json'}
#    )


#@ViewRegistrar('/api/v1/history/statistics')
#def api_v1_maintainer_problems(repo):
#    return (
#        dump_json(get_db().GetProblems(maintainer=maintainer)),
#        {'Content-type': 'application/json'}
#    )
