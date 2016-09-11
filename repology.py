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

import os
import subprocess

def Main():
    if not os.path.isfile('freebsd.list'):
        subprocess.check_call("wget -qO- http://www.FreeBSD.org/ports/INDEX-11.bz2 | bunzip2 > freebsd.list", shell = True)
    if not os.path.isfile('debian.list'):
        subprocess.check_call("wget -qO- http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz | gunzip > debian.list", shell = True)
    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
