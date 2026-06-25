# Copyright (C) 2024 Guilhem Saurel <guilhem.saurel@laas.fr>
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

from typing import Iterable

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from yaml import safe_load


def ros_extract_recipe_url(key, /, *, url, tags, version, **kwargs):
    release = tags['release'].format(
        package=key,
        version=version,
        upstream_version=version,
    )

    if 'github.com' in url:
        return url.removesuffix('.git') + f'/blob/{release}/package.xml'
    if 'gitlab' in url:
        return url.removesuffix('.git') + f'/-/blob/{release}/package.xml'
    if 'bitbucket' in url:
        # It is not possible to construct a bitbucket url for a file
        # on a specific tag
        return
    err = f'ROS package {key} is neither on github, gitlab, or bitbucket'
    raise RuntimeError(err)


class RosYamlParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path) as f:
            data = safe_load(f)
        for key, packagedata in data['repositories'].items():
            with factory.begin(key) as pkg:
                # Some included packages are not yet released,
                # and only available as source
                if 'release' not in packagedata:
                    pkg.log(f'dropping {key}: no release', severity=Logger.ERROR)
                    continue

                release = packagedata['release']

                if 'version' not in release:
                    pkg.log(f'dropping {key}: has no version.', severity=Logger.ERROR)
                    continue

                pkg.add_name(key, NameType.ROS_NAME)
                pkg.set_version(release['version'].split('-')[0])

                if recipe_url := ros_extract_recipe_url(key, **release):
                    pkg.add_links(LinkType.PACKAGE_RECIPE, recipe_url)
                else:
                    pkg.log(f'{key} has no known recipe url', severity=Logger.WARNING)

                if source := packagedata.get('source'):
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, source['url'])
                else:
                    pkg.log(f'{key} has no source', severity=Logger.WARNING)

                if doc := packagedata.get('doc'):
                    pkg.add_links(LinkType.UPSTREAM_DOCUMENTATION, doc['url'])

                yield pkg
