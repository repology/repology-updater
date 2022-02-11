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
    _hidden_maintainers: set[str]

    def __init__(self, maintainers_config: YamlConfig) -> None:
        self._hidden_maintainers = set()

        for maintainerdata in maintainers_config.get_items():
            maintainer: str | None = maintainerdata.get('maintainer')
            if maintainer is not None and maintainerdata.get('hide'):
                self._hidden_maintainers.add(maintainer)

    def is_hidden(self, maintainer: str) -> bool:
        return maintainer in self._hidden_maintainers
