# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
import re
from typing import Dict, Iterable

from libversion import version_compare

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


_WHITESPACE_PREFIX_RE = re.compile('([ ]*)[^ ]')
_KEYVAL_RE = re.compile('([a-zA-Z-]+)[ \t]*:[ \t]*(.*?)')


def _parse_cabal_file(path: str) -> Dict[str, str]:
    cabaldata: Dict[str, str] = {}
    offset = None
    key = None

    with open(path, 'r', encoding='utf-8') as cabalfile:
        for line in cabalfile:
            line = line.rstrip()

            # offset is needed to be calculated first, from first non-whitespace line
            if offset is None:
                match = _WHITESPACE_PREFIX_RE.match(line)
                if match:
                    offset = len(match.group(1))
                else:
                    continue

            line = line[offset:]

            # ignore comments
            if line.startswith('--'):
                continue

            # process multiline keys
            if key:
                if line.startswith(' '):
                    cabaldata[key] = cabaldata[key] + ' ' + line.strip() if key in cabaldata else line.strip()
                    continue
                else:
                    key = None

            # process singleline key or start of a multiline key
            match = _KEYVAL_RE.fullmatch(line)
            if not match:
                continue

            if match.group(2):
                cabaldata[match.group(1).lower()] = match.group(2)
            else:
                key = match.group(1).lower()

    return cabaldata


class HackageParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for moduledir in os.listdir(path):
            pkg = factory.begin()

            pkg.set_name(moduledir)

            modulepath = os.path.join(path, moduledir)

            cabalpath = None
            maxversion = None

            for versiondir in os.listdir(modulepath):
                if versiondir == 'preferred-versions':
                    continue

                if maxversion is None or version_compare(versiondir, maxversion) > 0:
                    maxversion = versiondir
                    cabalpath = os.path.join(path, moduledir, maxversion, moduledir + '.cabal')

            if maxversion is None:
                pkg.log('cannot determine max version'.format(), severity=Logger.ERROR)
                continue

            pkg.set_version(maxversion)

            assert(cabalpath)
            cabaldata = _parse_cabal_file(cabalpath)

            if cabaldata['name'] == pkg.name and version_compare(cabaldata['version'], pkg.version) == 0:
                pkg.set_summary(cabaldata.get('synopsis'))
                if 'maintainer' not in cabaldata:
                    pkg.add_maintainers('fallback-mnt-hackage@repology')
                else:
                    pkg.add_maintainers(extract_maintainers(cabaldata.get('maintainer')))
                pkg.add_licenses(cabaldata.get('license'))
                pkg.add_homepages(cabaldata.get('homepage'))
                pkg.add_categories(cabaldata.get('category'))
            else:
                pkg.log('cabal data sanity check failed ({} {} != {} {}), ignoring cabal data'.format(cabaldata['name'], cabaldata['version'], pkg.name, pkg.version), severity=Logger.ERROR)

            pkg.add_homepages('http://hackage.haskell.org/package/' + moduledir)

            yield pkg
