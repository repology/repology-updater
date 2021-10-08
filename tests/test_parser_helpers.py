# Copyright (C) 2016-2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import pytest

from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import EpochMode, nevra_construct, nevra_parse


class TestNevraConstruct:
    def test_basic(self):
        assert nevra_construct('foo', '1', '1.2.3', 'fc34.git20181111', 'src') == 'foo-1:1.2.3-fc34.git20181111.src'

    def test_epoch_mode_preserve(self):
        assert nevra_construct('foo', None, '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PRESERVE) == 'foo-1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', 0, '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PRESERVE) == 'foo-0:1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PRESERVE) == 'foo-1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '0', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PRESERVE) == 'foo-0:1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '1', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PRESERVE) == 'foo-1:1.2.3-fc34.git20181111.src'

    def test_epoch_mode_provide(self):
        assert nevra_construct('foo', None, '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PROVIDE) == 'foo-0:1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', 0, '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PROVIDE) == 'foo-0:1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PROVIDE) == 'foo-0:1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '0', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PROVIDE) == 'foo-0:1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '1', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.PROVIDE) == 'foo-1:1.2.3-fc34.git20181111.src'

    def test_epoch_mode_trim(self):
        assert nevra_construct('foo', None, '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.TRIM) == 'foo-1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', 0, '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.TRIM) == 'foo-1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.TRIM) == 'foo-1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '0', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.TRIM) == 'foo-1.2.3-fc34.git20181111.src'
        assert nevra_construct('foo', '1', '1.2.3', 'fc34.git20181111', 'src', epoch_mode=EpochMode.TRIM) == 'foo-1:1.2.3-fc34.git20181111.src'

    def test_partial(self):
        assert nevra_construct(None, '1', '1.2.3', 'fc34.git20181111', 'src') == '1:1.2.3-fc34.git20181111.src'

        assert nevra_construct('foo', None, '1.2.3', 'fc34.git20181111', 'src') == 'foo-1.2.3-fc34.git20181111.src'

        with pytest.raises(RuntimeError):
            nevra_construct('foo', '1', None, 'fc34.git20181111', 'src')  # type: ignore

        assert nevra_construct('foo', '1', '1.2.3', None, 'src') == 'foo-1:1.2.3.src'

        assert nevra_construct('foo', '1', '1.2.3', 'fc34.git20181111', None) == 'foo-1:1.2.3-fc34.git20181111'


class TestNevraParse:
    def test_basic(self):
        assert nevra_parse('foo-1.2.3-1.i386') == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-bar-baz-999:1.2.3-1.src') == ('foo-bar-baz', '999', '1.2.3', '1', 'src')

    def test_filename(self):
        assert nevra_parse('foo-1.2.3-1.i386.rpm') == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-bar-baz-999:1.2.3-1.src.rpm') == ('foo-bar-baz', '999', '1.2.3', '1', 'src')

    def test_epoch_mode_str_preserve(self):
        assert nevra_parse('foo-1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PRESERVE) == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-0:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PRESERVE) == ('foo', '0', '1.2.3', '1', 'i386')
        assert nevra_parse('foo-1:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PRESERVE) == ('foo', '1', '1.2.3', '1', 'i386')
        assert nevra_parse('foo-x:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PRESERVE) == ('foo', 'x', '1.2.3', '1', 'i386')

    def test_epoch_mode_str_provide(self):
        assert nevra_parse('foo-1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PROVIDE) == ('foo', '0', '1.2.3', '1', 'i386')
        assert nevra_parse('foo-0:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PROVIDE) == ('foo', '0', '1.2.3', '1', 'i386')
        assert nevra_parse('foo-1:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PROVIDE) == ('foo', '1', '1.2.3', '1', 'i386')
        assert nevra_parse('foo-x:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.PROVIDE) == ('foo', 'x', '1.2.3', '1', 'i386')

    def test_epoch_type_str_trim(self):
        assert nevra_parse('foo-1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.TRIM) == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-0:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.TRIM) == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-1:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.TRIM) == ('foo', '1', '1.2.3', '1', 'i386')
        assert nevra_parse('foo-x:1.2.3-1.i386', epoch_type=str, epoch_mode=EpochMode.TRIM) == ('foo', 'x', '1.2.3', '1', 'i386')

    def test_epoch_mode_int_preserve(self):
        assert nevra_parse('foo-1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PRESERVE) == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-0:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PRESERVE) == ('foo', 0, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-1:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PRESERVE) == ('foo', 1, '1.2.3', '1', 'i386')

        with pytest.raises(ValueError):
            nevra_parse('foo-x:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PRESERVE)

    def test_epoch_type_int_provide(self):
        assert nevra_parse('foo-1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PROVIDE) == ('foo', 0, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-0:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PROVIDE) == ('foo', 0, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-1:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PROVIDE) == ('foo', 1, '1.2.3', '1', 'i386')

        with pytest.raises(ValueError):
            nevra_parse('foo-x:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.PROVIDE)

    def test_epoch_type_int_trim(self):
        assert nevra_parse('foo-1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.TRIM) == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-0:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.TRIM) == ('foo', None, '1.2.3', '1', 'i386')
        assert nevra_parse('foo-1:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.TRIM) == ('foo', 1, '1.2.3', '1', 'i386')

        with pytest.raises(ValueError):
            nevra_parse('foo-x:1.2.3-1.i386', epoch_type=int, epoch_mode=EpochMode.TRIM)


class TestSplitMaintainers:
    def test_simple(self):
        assert extract_maintainers('amdmi3@FreeBSD.org') == ['amdmi3@freebsd.org']
        assert extract_maintainers('amdmi3@FAKE') == ['amdmi3@fake']

    def test_name(self):
        assert extract_maintainers('Dmitry Marakasov <amdmi3@FreeBSD.org>') == ['amdmi3@freebsd.org']
        assert extract_maintainers('"Dmitry Marakasov" <amdmi3@FreeBSD.org>') == ['amdmi3@freebsd.org']

    def test_name_comma(self):
        assert extract_maintainers('Marakasov, Dmitry <amdmi3@FreeBSD.org>') == ['amdmi3@freebsd.org']
        assert extract_maintainers('"Marakasov, Dmitry" <amdmi3@FreeBSD.org>') == ['amdmi3@freebsd.org']

    def test_lists(self):
        assert extract_maintainers('amdmi3@FreeBSD.org,gnome@FreeBSD.org') == ['amdmi3@freebsd.org', 'gnome@freebsd.org']
        assert extract_maintainers('amdmi3@FreeBSD.org, gnome@FreeBSD.org') == ['amdmi3@freebsd.org', 'gnome@freebsd.org']
        assert extract_maintainers('amdmi3@FreeBSD.org gnome@FreeBSD.org') == ['amdmi3@freebsd.org', 'gnome@freebsd.org']

    def test_list_name(self):
        assert extract_maintainers('Dmitry Marakasov <amdmi3@FreeBSD.org>, Gnome Guys <gnome@FreeBSD.org>') == ['amdmi3@freebsd.org', 'gnome@freebsd.org']

    def test_list_name_complex(self):
        assert extract_maintainers('Marakasov, Dmitry <amdmi3@FreeBSD.org>, Guys, Gnome <gnome@FreeBSD.org>') == ['amdmi3@freebsd.org', 'gnome@freebsd.org']

    def test_list_name_ambigous(self):
        # apart from samples form test_lists above, this is ambiguous -
        # words may be a name, or may be an obfuscated email. These
        # should be skipped
        assert extract_maintainers('dmitry marakasov amdmi3@FreeBSD.org, foo dot bar@FreeBSD.org') == []

    def test_garbage(self):
        assert extract_maintainers(',amdmi3@FreeBSD.org, ,,   ') == ['amdmi3@freebsd.org']

    def test_immune_to_obfuscation(self):
        assert extract_maintainers('amdmi3[at]FreeBSD[dot]org') == []
        assert extract_maintainers('amdmi3 [ at ] FreeBSD [ dot ] org') == []
        assert extract_maintainers('amdmi3 at FreeBSD dot org') == []
        assert extract_maintainers('amdmi3_at_FreeBSD.org') == []
        assert extract_maintainers('amdmi3{at}FreeBSD{dot}org') == []
        assert extract_maintainers('amdmi3 <at> freebsd {dot} org') == []
        assert extract_maintainers('amdmi3~at~freebsd~dot~org') == []
        assert extract_maintainers('amdmi3 (at) freebsd (dot) org') == []
        assert extract_maintainers('amdmi3 __at__ freebsd __dot__ org') == []
        assert extract_maintainers('amdmi3-at-freebsd-dot-org') == []
        assert extract_maintainers('amdmi3<at>freebsd.org') == []
        assert extract_maintainers('amdmi3 <at> freebsd.org') == []
        assert extract_maintainers('amdmi3 [underscore] ports [at] freebsd.org') == []
        assert extract_maintainers('amdmi3 plus ports@freebsd.org') == []
        assert extract_maintainers('agent smith (amdmi3@freebsd.org)') == []

        assert extract_maintainers('amdNOmi3@freeSPAMbsd.org (remove NO and SPAM)') == []
        assert extract_maintainers('amdmi3 @ google mail') == []

    def test_empty(self):
        assert extract_maintainers('somecrap') == []
        assert extract_maintainers('') == []
        assert extract_maintainers('http://repology.org') == []
        assert extract_maintainers('Repology <http://repology.org>') == []
        assert extract_maintainers('nobody <really>') == []
