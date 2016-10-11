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

from .freebsd import FreeBSDIndexParser
from .debian import DebianSourcesParser
from .gentoo import GentooGitParser
from .pkgsrc import PkgsrcIndexParser
from .openbsd import OpenBSDIndexParser
from .arch import ArchDBParser
from .spec import SpecParser
from .opensuse import OpenSUSERepodataParser
from .chocolatey import ChocolateyParser
from .sisyphus import SrcListClassicParser
from .slackbuilds import SlackBuildsParser
from .freshcode import FreshcodeParser
