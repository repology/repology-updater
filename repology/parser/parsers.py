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

from .anitya import AnityaApiParser
from .aports import ApkIndexParser
from .arch import ArchDBParser
from .aur import AURParser
from .chocolatey import ChocolateyParser
from .cpan import CPANPackagesParser
from .cran import CRANCheckSummaryParser
from .crux import CRUXParser
from .debian import DebianSourcesParser
from .distrowatch import DistrowatchPackagesParser
from .dports import DPortsIndexParser
from .fdroid import FDroidParser
from .freebsd import FreeBSDIndexParser
from .freshcode import FreshcodeParser
from .gentoo import GentooGitParser
from .gobolinux import GoboLinuxGitParser
from .guix import GuixParser
from .hackage import HackageParser
from .haiku import HaikuPortsFilenamesParser
from .homebrew import HomebrewJsonParser
from .libregamewiki import LibreGameWikiParser
from .macports import MacPortsParser
from .msys2 import MSYS2Parser
from .nix import NixJsonParser
from .openbsd import OpenBSDIndexParser
from .openindiana import OpenIndianaSummaryJsonParser
from .pkgsrc import PkgsrcIndexParser
from .pypi import PyPiHTMLParser
from .ravenports import RavenportsJsonParser
from .repodata import RepodataParser
from .rosa import RosaInfoXmlParser
from .rubygem import RubyGemParser
from .slackbuilds import SlackBuildsParser
from .snap import SnapJsonParser
from .spec import SpecParser
from .srclist import SrcListParser
from .yacp import YACPGitParser
