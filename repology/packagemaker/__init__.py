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

from abc import abstractmethod
from copy import deepcopy
from functools import wraps
from typing import Any, Callable, Iterable, Optional

from repology.logger import Logger
from repology.package import Package
from repology.packagemaker import normalizers as nzs


__all__ = ['PackageFactory', 'PackageMaker']


def _iter_unique(iterable, existing=None):
    seen = set(existing) if existing else set()
    for value in iterable:
        if value not in seen:
            seen.add(value)
            yield value


class PackageMakerBase(Logger):
    _logger: Logger

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    @abstractmethod
    def _get_ident(self) -> str:
        pass

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        self._logger._log(self._get_ident() + ': ' + message, severity, indent, prefix)

    @staticmethod
    def _flatten_args(args: Iterable[Any]) -> Iterable[Any]:
        for arg in args:
            if arg is None or arg == '':
                pass  # skip
            elif isinstance(arg, (str, int, float, bool)):
                yield arg  # scalar
            else:  # iterate
                yield from PackageMakerBase._flatten_args(arg)

    def _apply_normalizers(self, value, fieldname, normalizers):
        origvalue = value

        for normalizer in normalizers:
            if value is None:
                break

            value, error = normalizer(value)

            if error is not None:
                self.log('{}: "{}" {}'.format(fieldname, origvalue, error), Logger.ERROR if value is None else Logger.WARNING)

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
                if arg is None:
                    pass
                elif isinstance(arg, str) and want_type is int or isinstance(arg, int) and want_type is str:
                    arg = want_type(arg)
                elif not isinstance(arg, want_type):
                    raise RuntimeError('unexpected type {} for {} (expected {})'.format(arg.__class__.__name__, fieldname, want_type.__name__))
                value = self._apply_normalizers(arg, fieldname, normalizers)
                if value:
                    return method(self, value, *other_args)
            return wrapper
        return inner


class PackageMaker(PackageMakerBase):
    _package: Package
    _ident: Optional[str]
    _itemno: int
    _skipfailed: bool

    def __init__(self, logger: Logger, ident: Optional[str], itemno: int, skipfailed: bool = False) -> None:
        super(PackageMaker, self).__init__(logger)
        self._package = Package()
        self._ident = ident
        self._itemno = itemno
        self._skipfailed = skipfailed

    def _get_ident(self) -> str:
        return self._ident or self._package.extrafields.get('origin', None) or self._package.name or self._package.basename or 'item #{}'.format(self._itemno)

    @PackageMakerBase._simple_setter('origin', str, nzs.strip, nzs.forbid_newlines)
    def set_origin(self, origin: str) -> None:
        # XXX: convert to dedicated field
        self.set_extra_field('origin', origin)

    @PackageMakerBase._simple_setter('name', str, nzs.strip, nzs.forbid_newlines)
    def set_name(self, name: str) -> None:
        self._package.name = name

    @PackageMakerBase._simple_setter('basename', str, nzs.strip, nzs.forbid_newlines)
    def set_basename(self, basename: str) -> None:
        self._package.basename = basename

    def prefix_name(self, prefix: str) -> None:
        self._package.name = prefix + self._package.name

    @PackageMakerBase._simple_setter('version', str, nzs.strip, nzs.forbid_newlines)
    def set_version(self, version: str, version_normalizer: Optional[Callable[[str], str]] = None) -> None:
        self._package.rawversion = version
        self._package.origversion = version if version_normalizer is None else version_normalizer(version)
        self._package.version = self._package.origversion

    @PackageMakerBase._simple_setter('version', str, nzs.strip, nzs.forbid_newlines)
    def set_rawversion(self, rawversion: str) -> None:
        if rawversion != self._package.version:
            self._package.rawversion = rawversion

    def set_name_and_version(self, namever: str, version_normalizer: Optional[Callable[[str], str]] = None) -> None:
        name, version = namever.rsplit('-', 1)
        self.set_name(name)
        self.set_version(version, version_normalizer)

    @PackageMakerBase._simple_setter('arch', str, nzs.strip, nzs.forbid_newlines)
    def set_arch(self, arch: str) -> None:
        self._package.arch = arch

    @PackageMakerBase._simple_setter('summary', str, nzs.strip)
    def set_summary(self, summary: str) -> None:
        self._package.comment = summary

    @PackageMakerBase._omnivorous_setter('maintainer', str, nzs.strip, nzs.forbid_newlines, nzs.tolower)
    def add_maintainers(self, *args: Any) -> None:
        self._package.maintainers.extend(_iter_unique(args, self._package.maintainers))

    @PackageMakerBase._omnivorous_setter('category', str, nzs.strip, nzs.forbid_newlines)
    def add_categories(self, *args: Any) -> None:
        # XXX: convert into array
        if not self._package.category:
            self._package.category = args[0]

    @PackageMakerBase._omnivorous_setter('homepage', str, nzs.strip, nzs.url, nzs.warn_whitespace, nzs.forbid_newlines)
    def add_homepages(self, *args: Any) -> None:
        # XXX: convert into array
        if not self._package.homepage:
            self._package.homepage = args[0]

    @PackageMakerBase._omnivorous_setter('license', str, nzs.strip, nzs.forbid_newlines)
    def add_licenses(self, *args: Any) -> None:
        self._package.licenses.extend(args)

    @PackageMakerBase._omnivorous_setter('download', str, nzs.strip, nzs.url, nzs.warn_whitespace, nzs.forbid_newlines)
    def add_downloads(self, *args: Any) -> None:
        self._package.downloads.extend(_iter_unique(args, self._package.downloads))

    def set_flags(self, mask: int, is_set: bool = True) -> None:
        self._package.set_flag(mask, is_set)

    def set_extra_field(self, key: str, value: str) -> None:
        self._package.extrafields[key] = value

    def unwrap(self) -> Package:
        return self._package

    def clone(self, ident: Optional[str] = None, append_ident: Optional[str] = None) -> 'PackageMaker':
        offspring_ident = self._ident
        if ident is not None:
            offspring_ident = ident
        elif append_ident is not None:
            offspring_ident = (offspring_ident or '') + append_ident

        offspring = PackageMaker(self._logger, offspring_ident, self._itemno)
        offspring._package = deepcopy(self._package)

        return offspring

    def check_sanity(self, require_name: bool = True, require_version: bool = True, verbose: bool = False) -> bool:
        if require_name and not self._package.name:
            if verbose:
                self.log('package with no name', severity=Logger.ERROR)
            return False

        if require_version and not self._package.version:
            if verbose:
                self.log('package with no version', severity=Logger.ERROR)
            return False

        return True

    def __getattr__(self, key: str) -> Any:
        return getattr(self._package, key)

    def __enter__(self) -> 'PackageMaker':
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Optional[bool]:
        if exc_type:
            self.log('parsing failed ({}): {}: {}'.format(
                'skipped' if self._skipfailed else 'fatal',
                exc_type.__name__,
                exc_value
            ), severity=Logger.ERROR)

            if self._skipfailed:
                return True

        return None


class PackageFactory(Logger):
    _logger: Logger
    _itemno: int

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._itemno = 0

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        self._logger._log(message, severity, indent, prefix)

    def begin(self, ident: Optional[str] = None, skipfailed: bool = False) -> PackageMaker:
        self._itemno += 1
        return PackageMaker(self._logger, ident, self._itemno, skipfailed)
