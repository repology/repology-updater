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


__all__ = ['filename2nevra', 'construct_evr']


def filename2nevra(filename):
    rest, architecture, extension = filename.rsplit('.', 2)

    name, version, revision = rest.rsplit('-', 2)

    epoch = ''

    if ':' in version:
        epoch, version = version.rsplit(':', 1)

    return (name, epoch, version, revision, architecture)


def construct_evr(epoch, version, release):
    if not version:
        raise RuntimeError('no version provided`')

    evr = version

    if epoch and str(epoch) != '0':
        evr = str(epoch) + ':' + evr

    if release:
        evr = evr + '-' + release

    return evr
