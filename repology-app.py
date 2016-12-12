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

from repology.database import Database
from repology.repoman import RepositoryManager
from repology.package import ProduceRepositorySummary

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
database = Database("dbname=repology user=repology password=repology")

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

@app.route("/")
def main():
    return flask.render_template("layout.html")

@app.route("/metapackage/<name>")
def metapackage(name):
    packages = database.GetMetapackage(name)
    if not packages:
        flask.abort(404);

    packages = sorted(packages, key=lambda package: package.repo + package.name + package.version)
    repometadata = RepositoryManager("dummy").GetMetadata();
    return flask.render_template("package.html", packages=packages, repometadata=repometadata, name=name)

@app.route("/badge/all/<name>")
def badge_all(name):
    packages = database.GetMetapackage(name)
    if not packages:
        flask.abort(404);

    summaries = ProduceRepositorySummary(packages)
    repometadata = RepositoryManager("dummy").GetMetadata();

    repostates = []
    for reponame, summary in summaries.items():
        repostates.append({
            'name': repometadata[reponame]['desc'],
            'version': summary['version'],
            'versionclass': summary['versionclass']
        })

    return flask.render_template(
            "badge-big.svg",
            repositories=sorted(repostates, key=lambda repo: repo['name']),
            name=name
    )

@app.route("/news")
def news():
    return flask.render_template("news.html")

@app.route("/api/v1/metapackage/<name>")
def api_v1_metapackage(name):
    packages = [api_v1_package_to_json(package) for package in database.GetMetapackage(name)]
    if not packages:
        flask.abort(404)
    return (
        json.dumps(packages),
        {'Content-type': 'application/json'}
    )

@app.route("/api/v1/metapackages/", defaults={'name':''})
@app.route("/api/v1/metapackages/starting/<name>")
def api_v1_metapackages_starting(name):
    packages = [api_v1_package_to_json(package) for package in database.GetMetapackages(starting=name, limit=500)]
    return (
        json.dumps(packages),
        {'Content-type': 'application/json'}
    )

@app.route("/api/v1/metapackages/after/<name>")
def api_v1_metapackages_after(name):
    packages = [api_v1_package_to_json(package) for package in database.GetMetapackages(starting=name, limit=500)]
    return (
        json.dumps(packages),
        {'Content-type': 'application/json'}
    )

@app.route("/api/v1/metapackages/before/<name>")
def api_v1_metapackages_before(name):
    packages = [api_v1_package_to_json(package) for package in database.GetMetapackages(starting=name, limit=500)]
    return (
        json.dumps(packages),
        {'Content-type': 'application/json'}
    )

if __name__ == "__main__":
    app.run()
