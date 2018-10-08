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


__all__ = ['nevra_construct', 'nevra_parse', 'EpochMode']


class EpochMode:
    PRESERVE = 0
    PROVIDE = 1
    TRIM = 2


def nevra_parse(nevra, epoch_mode=EpochMode.PRESERVE, epoch_type=str):
    (name, epoch, version, release, architecture) = (None, None, None, None, None)

    rest = nevra

    if rest.endswith('.rpm'):
        rest = rest[:-4]

    rest, architecture = rest.rsplit('.', 1)

    name, version, release = rest.rsplit('-', 2)

    if ':' in version:
        epoch, version = version.rsplit(':', 1)

    if epoch_mode == EpochMode.TRIM and epoch is not None and epoch == '0':
        epoch = None

    if epoch_mode == EpochMode.PROVIDE and epoch is None:
        epoch = '0'

    if epoch_type is int and epoch is not None:
        epoch = int(epoch)

    return (name, epoch, version, release, architecture)


def nevra_construct(name, epoch, version, release=None, architecture=None, epoch_mode=EpochMode.TRIM):
    result = ''

    if version is None:
        raise RuntimeError('version os required')

    result = version

    if epoch_mode == EpochMode.TRIM and epoch in ('', '0', 0):
        epoch = None

    if epoch_mode == EpochMode.PROVIDE and (not epoch or epoch == '0'):
        epoch = '0'

    if epoch is not None and epoch != '':
        result = str(epoch) + ':' + result

    if release is not None:
        result = result + '-' + release

    if name is not None:
        result = name + '-' + result

    if architecture is not None:
        result = result + '.' + architecture

    return result


def parse_nevra_from_filename(filename):
    # just drop extension; assumes extension does not contain
    # extra dots, e.g. .rpm, not .tar.gz
    return parse_nevra(filename.rsplit('.', 1)[0])


def parse_nevra(nevra):
    rest, architecture = nevra.rsplit('.', 1)

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
