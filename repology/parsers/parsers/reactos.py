# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import configparser
import os

from repology.parsers import Parser


class RappsParser(Parser):
    def iter_parse(self, path, factory):
        for filename in os.listdir(os.path.join(path)):
            if not filename.endswith('.txt'):
                continue

            pkg = factory.begin(filename)

            config = configparser.ConfigParser(interpolation=None)
            config.read(os.path.join(path, filename))

            config = config['Section']

            pkg.set_name(filename[:-4])
            pkg.set_version(config.get('Version'))
            pkg.set_summary(config['Description'])
            pkg.add_homepages(config.get('URLSite'))
            pkg.add_downloads(config['URLDownload'])
            pkg.add_licenses(config.get('License'))

            pkg.set_extra_field('longname', config['Name'])

            yield pkg
