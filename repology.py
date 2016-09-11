#!/usr/bin/env python3

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
