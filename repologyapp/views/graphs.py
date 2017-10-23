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

import math

import flask

from repologyapp.globals import *
from repologyapp.graphprocessor import GraphProcessor
from repologyapp.math import safe_percent
from repologyapp.view_registry import ViewRegistrar

from repology.config import config


def graph_generic(getgraph, color, suffix=''):
    # use autoscaling until history is filled
    numdays = 21
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


@ViewRegistrar('/graph/repo/<repo>/metapackages_total.svg')
def graph_repo_metapackages_total(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages'], '#000000')


@ViewRegistrar('/graph/repo/<repo>/metapackages_newest.svg')
def graph_repo_metapackages_newest(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_newest'], '#5cb85c')


@ViewRegistrar('/graph/repo/<repo>/metapackages_newest_percent.svg')
def graph_repo_metapackages_newest_percent(repo):
    return graph_repo_generic(repo, lambda s: safe_percent(s['num_metapackages_newest'], s['num_metapackages'] - s['num_metapackages_unique']), '#5cb85c', '%')


@ViewRegistrar('/graph/repo/<repo>/metapackages_outdated.svg')
def graph_repo_metapackages_outdated(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_outdated'], '#d9534f')


@ViewRegistrar('/graph/repo/<repo>/metapackages_outdated_percent.svg')
def graph_repo_metapackages_outdated_percent(repo):
    return graph_repo_generic(repo, lambda s: safe_percent(s['num_metapackages_outdated'], s['num_metapackages'] - s['num_metapackages_unique']), '#d9534f', '%')


@ViewRegistrar('/graph/repo/<repo>/metapackages_unique.svg')
def graph_repo_metapackages_unique(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_unique'], '#5bc0de')


@ViewRegistrar('/graph/repo/<repo>/metapackages_unique_percent.svg')
def graph_repo_metapackages_unique_percent(repo):
    return graph_repo_generic(repo, lambda s: s['num_metapackages_unique'] / s['num_metapackages'] * 100.0, '#5bc0de', '%')


@ViewRegistrar('/graph/repo/<repo>/problems.svg')
def graph_repo_problems(repo):
    return graph_repo_generic(repo, lambda s: s['num_problems'], '#c00000')


@ViewRegistrar('/graph/repo/<repo>/problems_per_metapackage.svg')
def graph_repo_problems_per_metapackage(repo):
    return graph_repo_generic(repo, lambda s: s['num_problems'] / s['num_metapackages'], '#c00000')


@ViewRegistrar('/graph/repo/<repo>/maintainers.svg')
def graph_repo_maintainers(repo):
    return graph_repo_generic(repo, lambda s: s['num_maintainers'], '#c000c0')


@ViewRegistrar('/graph/repo/<repo>/packages_per_maintainer.svg')
def graph_repo_packages_per_maintainer(repo):
    return graph_repo_generic(repo, lambda s: s['num_packages'] / s['num_maintainers'], '#c000c0')


@ViewRegistrar('/graph/total/packages.svg')
def graph_total_packages():
    return graph_total_generic(lambda s: s['num_packages'], '#000000')


@ViewRegistrar('/graph/total/metapackages.svg')
def graph_total_metapackages():
    return graph_total_generic(lambda s: s['num_metapackages'], '#000000')


@ViewRegistrar('/graph/total/maintainers.svg')
def graph_total_maintainers():
    return graph_total_generic(lambda s: s['num_maintainers'], '#c000c0')


@ViewRegistrar('/graph/total/problems.svg')
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


@ViewRegistrar('/graph/map_repo_size_fresh.svg')
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


@ViewRegistrar('/graph/map_repo_size_fresh_nonunique.svg')
def graph_map_repo_size_fresh_nonunique():
    def repo2coords(repo):
        return {
            'x': repo['num_metapackages_newest'] + repo['num_metapackages_outdated'],
            'y': repo['num_metapackages_newest']
        }

    return map_repo_generic(
        repo2coords,
        namex='Number of non-unique packages in repository',
        namey='Number of fresh packages in repository'
    )


@ViewRegistrar('/graph/map_repo_size_freshness.svg')
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
