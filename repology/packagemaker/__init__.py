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

from copy import deepcopy
from functools import wraps

from repology.logger import Logger
from repology.package import Package
from repology.packagemaker import normalizers as nzs


__all__ = ['PackageFactory', 'PackageMaker']


class PackageMakerBase:
    def __init__(self, logger):
        self.logger = logger

    def _get_ident(self):
        return '?'

    def log(self, message, severity=Logger.NOTICE):
        self.logger.log(self._get_ident() + ': ' + message, severity)

    @staticmethod
    def _flatten_args(args):
        for arg in args:
            if isinstance(arg, list):
                yield from PackageMakerBase._flatten_args(arg)
            elif arg is not None and arg != '':
                yield arg

    def _apply_normalizers(self, value, fieldname, normalizers):
        origvalue = value

        for normalizer in normalizers:
            value, error = normalizer(value)

            if error is not None:
                self.log('{}: "{}" {}'.format(fieldname, origvalue, error), Logger.ERROR if value is None else Logger.WARNING)

            if value is None:
                return None

        return value

    def _normalize_args(self, args, fieldname, want_type, normalizers):
        output = []
        for arg in PackageMakerBase._flatten_args(args):
            if not isinstance(arg, want_type):
                self.log('{}: "{}" expected type {}, got {}'.format(fieldname, arg, want_type.__name__, arg.__class__.__name__))
                return None

            value = self._apply_normalizers(arg, fieldname, normalizers)
            if value is not None:
                output.append(value)

        return output

    def _omnivorous_setter(fieldname, want_type, *normalizers):  # noqa: N805
        def inner(method):
            @wraps(method)
            def wrapper(self, *args):
                values = self._normalize_args(args, fieldname, want_type, normalizers)
                if values:
                    return method(self, *values)
            return wrapper
        return inner

    def _simple_setter(fieldname, want_type, *normalizers):  # noqa: N805
        def inner(method):
            @wraps(method)
            def wrapper(self, arg, *other_args):
                value = self._apply_normalizers(arg, fieldname, normalizers)
                if value:
                    return method(self, value, *other_args)
            return wrapper
        return inner


class PackageMaker(PackageMakerBase):
    def __init__(self, logger, ident):
        super(PackageMaker, self).__init__(logger)
        self.package = Package()
        self.ident = ident

    def _get_ident(self):
        return self.package.extrafields.get('origin', None) or self.package.name or self.ident or self.package.effname

    @PackageMakerBase._simple_setter('origin', str, nzs.strip, nzs.forbid_newlines)
    def set_origin(self, origin):
        # XXX: convert to dedicated field
        self.set_extra_field('origin', origin)

    @PackageMakerBase._simple_setter('name', str, nzs.strip, nzs.forbid_newlines)
    def set_effname(self, effname):
        # XXX: this should be refactored
        # It's OK for parsers to set both effname and name, the example case
        # is setting effname to <project> name and <name>s to package names
        # However this erases strict boundary between fields parsed from
        # data and fields calculated based on them. It should be fixed.
        self.package.effname = effname

    @PackageMakerBase._simple_setter('name', str, nzs.strip, nzs.forbid_newlines)
    def set_name(self, name):
        self.package.name = name

    @PackageMakerBase._simple_setter('version', str, nzs.strip, nzs.forbid_newlines)
    def set_version(self, version, version_normalizer=None):
        if version_normalizer is None:
            self.package.version = version
        else:
            normalized_version = version_normalizer(version)

            # XXX: compatibility shim to allow old style SanitizeVesion returning version and origversion
            if isinstance(normalized_version, tuple):
                normalized_version = normalized_version[0]

            if normalized_version == version:
                self.package.version = version
            else:
                self.package.version = normalized_version
                self.package.origversion = version

    @PackageMakerBase._simple_setter('version', str, nzs.strip, nzs.forbid_newlines)
    def set_origversion(self, origversion):
        if origversion != self.package.version:
            self.package.origversion = origversion

    def set_name_and_version(self, namever, version_normalizer=None):
        name, version = namever.rsplit('-', 1)
        self.set_name(name)
        self.set_version(version, version_normalizer)

    @PackageMakerBase._simple_setter('summary', str, nzs.strip)
    def set_summary(self, summary):
        self.package.comment = summary

    @PackageMakerBase._omnivorous_setter('maintainer', str, nzs.strip, nzs.forbid_newlines)
    def add_maintainers(self, *args):
        self.package.maintainers.extend(args)

    @PackageMakerBase._omnivorous_setter('category', str, nzs.strip, nzs.forbid_newlines)
    def add_categories(self, *args):
        # XXX: convert into array
        if not self.package.category:
            self.package.category = args[0]

    @PackageMakerBase._omnivorous_setter('homepage', str, nzs.strip, nzs.require_url, nzs.warn_whitespace, nzs.forbid_newlines)
    def add_homepages(self, *args):
        # XXX: convert into array
        if not self.package.homepage:
            self.package.homepage = args[0]

    @PackageMakerBase._omnivorous_setter('license', str, nzs.strip, nzs.forbid_newlines)
    def add_licenses(self, *args):
        self.package.licenses.extend(args)

    @PackageMakerBase._omnivorous_setter('download', str, nzs.strip, nzs.require_url, nzs.warn_whitespace, nzs.forbid_newlines)
    def add_downloads(self, *args):
        self.package.downloads.extend(args)

    def set_flags(self, mask, is_set=True):
        assert(isinstance(mask, int))
        assert(isinstance(is_set, bool))
        self.package.SetFlag(mask, is_set)

    def set_extra_field(self, key, value):
        assert(isinstance(key, str))
        assert(isinstance(value, str))
        self.package.extrafields[key] = value

    def unwrap(self):
        return self.package

    def clone(self):
        offspring = PackageMaker(self.logger, self.ident)
        offspring.package = deepcopy(self.package)
        return offspring

    def check_sanity(self, verbose=False):
        if not self.package.name:
            if verbose:
                self.log('package with no name', severity=Logger.ERROR)
            return False

        if not self.package.version:
            if verbose:
                self.log('package with no version', severity=Logger.ERROR)
            return False

        return True

    def __getattr__(self, key):
        return getattr(self.package, key)

    # XXX: compatibility shim
    def __setattr__(self, key, value):
        if key in ['package', 'logger', 'ident']:
            return super(PackageMaker, self).__setattr__(key, value)
        return setattr(self.package, key, value)


class PackageFactory:
    def __init__(self, logger):
        self.logger = logger
        self.itemno = 0

    def begin(self, ident=None):
        self.itemno += 1
        return PackageMaker(self.logger, ident or 'item #{}'.format(self.itemno))

    def log(self, message, severity=Logger.NOTICE):
        self.logger.log(message, severity)
