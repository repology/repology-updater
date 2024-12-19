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
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


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


class RosYamlParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path) as f:
            data = load(f, Loader=Loader)
        for key, packagedata in data['repositories'].items():
            with factory.begin(key) as pkg:
                # Some included packages are not yet released,
                # and only available as source
                if 'release' not in packagedata:
                    pkg.log(f'dropping {pkg}: no release', severity=Logger.ERROR)
                    continue

                release = packagedata['release']

                if 'version' not in release:
                    pkg.log(f'dropping {pkg}: has no version.', severity=Logger.ERROR)
                    continue

                if 'bitbucket' in release['url']:
                    pkg.log(f'dropping {pkg}: RIP bitbucket', severity=Logger.ERROR)
                    continue

                pkg.add_name(key, NameType.ROS_NAME)
                pkg.set_version(release['version'].split('-')[0])

                if recipe_url := ros_extract_recipe_url(key, **release):
                    pkg.add_links(LinkType.PACKAGE_RECIPE, recipe_url)
                else:
                    pkg.log(f'{pkg} has no known recipe url', severity=Logger.WARNING)

                if source := packagedata.get('source'):
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, source['url'])
                else:
                    pkg.log(f'{pkg} has no source', severity=Logger.WARNING)

                if doc := packagedata.get('doc'):
                    pkg.add_links(LinkType.UPSTREAM_DOCUMENTATION, doc['url'])

                yield pkg
