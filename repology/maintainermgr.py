# Copyright (C) 2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.yamlloader import YamlConfig


class MaintainerManager:
    _maintainers_map: dict[str, str | None]

    def __init__(self, maintainers_config: YamlConfig) -> None:
        self._maintainers_map = dict()

        for maintainer_data in maintainers_config.get_items():
            maintainer = maintainer_data['maintainer']
            if maintainer_data.get('hide', False):
                self._maintainers_map[maintainer] = None
            elif (replacement := maintainer_data.get('replace')) is not None:
                self._maintainers_map[maintainer] = replacement

    def is_hidden(self, maintainer: str) -> bool:
        return self.convert_maintainer(maintainer) is None

    def convert_maintainer(self, maintainer: str) -> str | None:
        return self._maintainers_map.get(maintainer, maintainer)
