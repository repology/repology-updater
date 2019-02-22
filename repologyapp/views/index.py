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

import flask

from repologyapp.db import get_db
from repologyapp.globals import repometadata
from repologyapp.math import safe_percent
from repologyapp.metapackages import packages_to_summary_items
from repologyapp.view_registry import ViewRegistrar


@ViewRegistrar('/')
def index():
    repostats = [
        repo for repo in get_db().get_active_repositories()
        if repometadata[repo['name']]['type'] == 'repository'
    ]

    top_repos = {
        'by_total': [
            {
                'name': repo['name'],
                'value': repo['num_metapackages'],
            }
            for repo in sorted(repostats, key=lambda repo: repo['num_metapackages'], reverse=True)
        ][:10],
        'by_nonunique': [
            {
                'name': repo['name'],
                'value': repo['num_metapackages'] - repo['num_metapackages_unique'],
            }
            for repo in sorted(repostats, key=lambda repo: repo['num_metapackages'] - repo['num_metapackages_unique'], reverse=True)
        ][:10],
        'by_newest': [
            {
                'name': repo['name'],
                'value': repo['num_metapackages_newest'],
            }
            for repo in sorted(repostats, key=lambda repo: repo['num_metapackages_newest'], reverse=True)
        ][:10],
        'by_pnewest': [
            {
                'name': repo['name'],
                'value': '{:.2f}%'.format(safe_percent(repo['num_metapackages_newest'], repo['num_metapackages_comparable'])),
            }
            for repo in sorted(repostats, key=lambda repo: safe_percent(repo['num_metapackages_newest'], repo['num_metapackages_comparable']), reverse=True)
            if repo['num_metapackages'] > 1000
        ][:8]
    }

    important_packages = [
        'apache24',
        'awesome',
        'bash',
        'binutils',
        'bison',
        'blender',
        'boost',
        'bzip2',
        'chromium',
        'claws-mail',
        'cmake',
        'cppcheck',
        'cups',
        'curl',
        'darktable',
        'dia',
        'djvulibre',
        'dosbox',
        'dovecot',
        'doxygen',
        'dvd+rw-tools',
        'emacs',
        'exim',
        'ffmpeg',
        'firefox',
        'flex',
        'fluxbox',
        'freecad',
        'freetype',
        'gcc',
        'gdb',
        'geeqie',
        'gimp',
        'git',
        'gnupg',
        'go',
        'graphviz',
        'grub',
        'icewm',
        'imagemagick',
        'inkscape',
        'irssi',
        'kodi',
        'lame',
        'lftp',
        'libreoffice',
        'libressl',
        'lighttpd',
        'links',
        'llvm',
        'mariadb',
        'maxima',
        'mc',
        'memcached',
        'mercurial',
        'mesa',
        'mplayer',
        'mutt',
        'mysql',
        'nginx',
        'nmap',
        'octave',
        'openbox',
        'openssh',
        'openssl',
        'openttf',
        'openvpn',
        'p7zip',
        'perl',
        'pidgin',
        'postfix',
        'postgresql',
        'privoxy',
        'procmail',
        'python3',
        'qemu',
        'rdesktop',
        'redis',
        'rrdtool',
        'rsync',
        'rtorrent',
        'rxvt-unicode',
        'samba',
        'sane-backends',
        'scons',
        'screen',
        'scribus',
        'scummvm',
        'sdl2',
        'smartmontools',
        'sqlite3',
        'squid',
        'subversion',
        'sudo',
        'sumversion',
        'thunderbird',
        'tigervnc',
        'tmux',
        'tor',
        'valgrind',
        'vim',
        'virtualbox',
        'vlc',
        'vsftpd',
        'wayland',
        'wesnoth',
        'wget',
        'wine',
        'wireshark',
        'xorg-server',
        'youtube-dl',
        'zsh',
    ]

    metapackages = get_db().get_metapackages(important_packages)

    packages = get_db().get_metapackages_packages(important_packages, fields=['family', 'effname', 'version', 'versionclass', 'flags'])

    metapackagedata = packages_to_summary_items(packages)

    return flask.render_template(
        'index.html',
        top_repos=top_repos,
        metapackages=metapackages,
        metapackagedata=metapackagedata
    )
