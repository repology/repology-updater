# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import ClassVar, Optional, Type, Union

__all__ = ['nevra_construct', 'nevra_parse', 'EpochMode']


class EpochMode:
    PRESERVE: ClassVar[int] = 0
    PROVIDE: ClassVar[int] = 1
    TRIM: ClassVar[int] = 2


# XXX: use typevar
# https://github.com/python/mypy/issues/4236
#EpochType = TypeVar('EpochType', str, int)

def nevra_parse(nevra: str, epoch_mode: int = EpochMode.PRESERVE, epoch_type: Type[Union[str, int]] = str) -> tuple[str, Union[int, str, None], str, str, str]:
    epoch: Union[int, str, None] = None

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


def nevra_construct(name: Optional[str], epoch: Union[str, int, None], version: str, release: Optional[str] = None, architecture: Optional[str] = None, epoch_mode: int = EpochMode.TRIM) -> str:
    result = ''

    if version is None:
        raise RuntimeError('version is required')

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
