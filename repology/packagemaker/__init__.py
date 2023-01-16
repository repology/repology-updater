# Copyright (C) 2018-2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import warnings
from abc import abstractmethod
from copy import deepcopy
from functools import wraps
from typing import Any, Callable, Iterable, Type, TypeVar

from repology.logger import Logger, NoopLogger
from repology.package import LinkType, Package, PackageLinkTuple, PackageStatus
from repology.packagemaker import normalizers as nzs
from repology.packagemaker.names import NameMapper
from repology.packagemaker.names import NameType as NameType
from repology.packagemaker.normalizers import NormalizerFunction
from repology.utils.itertools import unicalize


__all__ = ['NameType', 'PackageFactory', 'PackageMaker']


_MAX_URL_LENGTH = 2047
_MAX_SUMMARY_LENGTH = 1024


class PackageTemplate:
    __slots__ = [
        'subrepo',

        'version',
        'origversion',
        'rawversion',

        'binnames',

        'arch',
        'summary',
        'maintainers',
        'categories',
        'licenses',

        'flags',

        'extrafields',

        'cpe_vendor',
        'cpe_product',
        'cpe_edition',
        'cpe_lang',
        'cpe_sw_edition',
        'cpe_target_sw',
        'cpe_target_hw',
        'cpe_other',

        'flavors',

        'links',
    ]

    subrepo: str | None

    version: str | None
    origversion: str | None
    rawversion: str | None

    binnames: list[str]

    arch: str | None
    summary: str | None
    maintainers: list[str]
    categories: list[str]
    licenses: list[str]

    flags: int

    extrafields: dict[str, Any]

    cpe_vendor: str | None
    cpe_product: str | None
    cpe_edition: str | None
    cpe_lang: str | None
    cpe_sw_edition: str | None
    cpe_target_sw: str | None
    cpe_target_hw: str | None
    cpe_other: str | None

    flavors: list[str]

    links: list[PackageLinkTuple]

    def __init__(self) -> None:
        self.subrepo = None

        self.version = None
        self.origversion = None
        self.rawversion = None

        self.binnames = []

        self.arch = None
        self.summary = None
        self.maintainers = []
        self.categories = []
        self.licenses = []

        self.flags = 0

        self.extrafields = {}

        self.cpe_vendor = None
        self.cpe_product = None
        self.cpe_edition = None
        self.cpe_lang = None
        self.cpe_sw_edition = None
        self.cpe_target_sw = None
        self.cpe_target_hw = None
        self.cpe_other = None

        self.flavors = []

        self.links = []


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

    def _apply_normalizers(self, value: str | None, fieldname: str, normalizers: Iterable[NormalizerFunction]) -> str | None:
        origvalue = value

        for normalizer in normalizers:
            if value is None:
                break

            value, error = normalizer(value)

            if error is not None:
                self.log('{}: "{}" {}'.format(fieldname, origvalue, error), Logger.ERROR if value is None else Logger.WARNING)

        return value

    def _normalize_args(self, args: Iterable[Any], fieldname: str, want_type: Any, normalizers: Iterable[NormalizerFunction]) -> list[Any] | None:
        output = []
        for arg in PackageMakerBase._flatten_args(args):
            if not isinstance(arg, want_type):
                self.log('{}: "{}" expected type {}, got {}'.format(fieldname, arg, want_type.__name__, arg.__class__.__name__))
                return None

            value = self._apply_normalizers(arg, fieldname, normalizers)
            if value is not None:
                output.append(value)

        return output


def _omnivorous_setter(fieldname: str, want_type: Type[Any], *normalizers: NormalizerFunction) -> Callable[[Callable[..., Any]], Any]:
    def inner(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(self: PackageMakerBase, *args: Any) -> Any:
            values = self._normalize_args(args, fieldname, want_type, normalizers)
            if values:
                return method(self, *values)
        return wrapper
    return inner


def _simple_setter(fieldname: str, want_type: Type[Any], *normalizers: NormalizerFunction) -> Callable[[Callable[..., Any]], Any]:
    def inner(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(self: PackageMakerBase, arg: Any, *other_args: Any) -> Any:
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


T = TypeVar('T')


class PackageMaker(PackageMakerBase):
    _package: PackageTemplate
    _name_mapper: NameMapper
    _ident: str | None
    _itemno: int
    _skipfailed: bool

    def __init__(self, logger: Logger, ident: str | None, itemno: int, skipfailed: bool = False) -> None:
        super(PackageMaker, self).__init__(logger)
        self._package = PackageTemplate()
        self._name_mapper = NameMapper()
        self._ident = ident
        self._itemno = itemno
        self._skipfailed = skipfailed

    def _get_ident(self) -> str:
        return self._ident or self._name_mapper.describe() or 'item #{}'.format(self._itemno)

    @_simple_setter('name', str, nzs.strip, nzs.forbid_newlines)
    def add_name(self, name: str, name_type: int) -> None:
        self._name_mapper.add_name(name, name_type)

    @_omnivorous_setter('binname', str, nzs.strip, nzs.forbid_newlines)
    def add_binnames(self, *args: Any) -> None:
        self._package.binnames.extend(args)

    @_simple_setter('version', str, nzs.strip, nzs.forbid_newlines)
    def set_version(self, version: str, version_normalizer: Callable[[str], str] | None = None) -> None:
        self._package.rawversion = version
        self._package.origversion = version if version_normalizer is None else version_normalizer(version)
        self._package.version = self._package.origversion

    @_simple_setter('version', str, nzs.strip, nzs.forbid_newlines)
    def set_rawversion(self, rawversion: str) -> None:
        if rawversion != self._package.version:
            self._package.rawversion = rawversion

    @_simple_setter('arch', str, nzs.strip, nzs.forbid_newlines)
    def set_arch(self, arch: str) -> None:
        self._package.arch = arch

    @_simple_setter('subrepo', str, nzs.strip, nzs.forbid_newlines)
    def set_subrepo(self, subrepo: str) -> None:
        self._package.subrepo = subrepo

    @_simple_setter('summary', str, nzs.strip, nzs.limit_length(_MAX_SUMMARY_LENGTH))
    def set_summary(self, summary: str) -> None:
        self._package.summary = summary

    @_omnivorous_setter('maintainer', str, nzs.strip, nzs.forbid_newlines, nzs.tolower)
    def add_maintainers(self, *args: Any) -> None:
        self._package.maintainers.extend(args)

    @_omnivorous_setter('category', str, nzs.strip, nzs.forbid_newlines)
    def add_categories(self, *args: Any) -> None:
        self._package.categories.extend(args)

    @_omnivorous_setter('homepage', str, nzs.strip, nzs.url, nzs.warn_whitespace, nzs.forbid_newlines, nzs.limit_length(_MAX_URL_LENGTH))
    def add_homepages(self, *args: Any) -> None:
        warnings.warn('Use add_links(LinkType.UPSTREAM_HOMEPAGE, ...) instead of add_homepages(...)', DeprecationWarning, stacklevel=3)
        self.add_links(LinkType.UPSTREAM_HOMEPAGE, args)

    @_omnivorous_setter('license', str, nzs.strip, nzs.forbid_newlines)
    def add_licenses(self, *args: Any) -> None:
        self._package.licenses.extend(args)

    @_omnivorous_setter('download', str, nzs.strip, nzs.url, nzs.warn_whitespace, nzs.forbid_newlines, nzs.limit_length(_MAX_URL_LENGTH))
    def add_downloads(self, *args: Any) -> None:
        warnings.warn('Use add_links(LinkType.UPSTREAM_DOWNLOAD, ...) instead of add_downloads(...)', DeprecationWarning, stacklevel=3)
        self.add_links(LinkType.UPSTREAM_DOWNLOAD, args)

    @_omnivorous_setter('flavor', str, nzs.strip, nzs.warn_whitespace, nzs.forbid_newlines)
    def add_flavors(self, *args: Any) -> None:
        self._package.flavors.extend(args)

    def add_links(self, link_type: int, *args: Any) -> None:
        link_normalizers = [
            nzs.strip,
            nzs.url,
            nzs.warn_whitespace,
            nzs.forbid_newlines,
            nzs.limit_length(_MAX_URL_LENGTH)
        ]

        urls = self._normalize_args(args, 'link', str, link_normalizers)

        if urls:
            self._package.links.extend((link_type, *url.rstrip('#').split('#', 1)) for url in urls)  # type: ignore

    def set_flags(self, mask: int, is_set: bool = True) -> None:
        if is_set:
            self._package.flags |= mask
        else:
            self._package.flags &= ~mask

    def set_extra_field(self, key: str, value: Any) -> None:
        self._package.extrafields[key] = value

    def add_cpe(self, vendor: str | None = None, product: str | None = None, edition: str | None = None, lang: str | None = None, sw_edition: str | None = None, target_sw: str | None = None, target_hw: str | None = None, other: str | None = None) -> None:
        self._package.cpe_vendor = vendor
        self._package.cpe_product = product
        self._package.cpe_edition = edition
        self._package.cpe_lang = lang
        self._package.cpe_sw_edition = sw_edition
        self._package.cpe_target_sw = target_sw
        self._package.cpe_target_hw = target_hw
        self._package.cpe_other = other

    def spawn(self, repo: str, family: str, subrepo: str | None = None, shadow: bool = False, default_maintainer: str | None = None) -> Package:
        maintainers: list[str] | None = None

        if self._package.maintainers:
            maintainers = list(unicalize(self._package.maintainers)) or None
        elif default_maintainer:
            maintainers = [default_maintainer]

        names = self._name_mapper.get_mapped_names()

        if names.name is None and names.srcname is None and names.binname is None:
            raise RuntimeError('Attempt to spawn Package without any name (name, binname, srcname) set')
        if names.trackname is None:
            raise RuntimeError('Attempt to spawn Package with unset trackname')
        if names.visiblename is None:
            raise RuntimeError('Attempt to spawn Package with unset visiblename')
        if names.projectname_seed is None:
            raise RuntimeError('Attempt to spawn Package with unset projectname_seed')
        if self._package.version is None:
            raise RuntimeError('Attempt to spawn Package with unset version')

        return Package(
            repo=repo,
            family=family,
            subrepo=self._package.subrepo or subrepo,

            name=names.name,
            srcname=names.srcname,
            binname=names.binname,
            binnames=list(unicalize(self._package.binnames)) or None,
            trackname=names.trackname,
            visiblename=names.visiblename,
            projectname_seed=names.projectname_seed,

            version=self._package.version,
            origversion=self._package.version,
            rawversion=self._package.rawversion if self._package.rawversion is not None else self._package.version,

            arch=self._package.arch,

            maintainers=maintainers,
            category=self._package.categories[0] if self._package.categories else None,  # TODO: convert to array
            comment=self._package.summary,
            licenses=list(unicalize(self._package.licenses)) or None,

            flags=self._package.flags,
            shadow=shadow,

            extrafields=self._package.extrafields if self._package.extrafields else None,

            cpe_vendor=self._package.cpe_vendor,
            cpe_product=self._package.cpe_product,
            cpe_edition=self._package.cpe_edition,
            cpe_lang=self._package.cpe_lang,
            cpe_sw_edition=self._package.cpe_sw_edition,
            cpe_target_sw=self._package.cpe_target_sw,
            cpe_target_hw=self._package.cpe_target_hw,
            cpe_other=self._package.cpe_other,

            flavors=list(unicalize(self._package.flavors)),  # TODO: convert to string

            links=list(unicalize(self._package.links)) or None,

            # XXX: see comment for PackageStatus.UNPROCESSED
            # XXX: duplicate code: PackageTransformer does the same
            effname=names.projectname_seed,
            versionclass=PackageStatus.UNPROCESSED,
        )

    def clone(self, ident: str | None = None, append_ident: str | None = None) -> 'PackageMaker':
        offspring_ident = self._ident
        if ident is not None:
            offspring_ident = ident
        elif append_ident is not None:
            offspring_ident = (offspring_ident or '') + append_ident

        offspring = PackageMaker(self._logger, offspring_ident, self._itemno)
        offspring._package = deepcopy(self._package)
        offspring._name_mapper = deepcopy(self._name_mapper)

        return offspring

    def __getattr__(self, key: str) -> Any:
        return getattr(self._package, key)

    def __enter__(self) -> 'PackageMaker':
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool | None:
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

    def __init__(self, logger: Logger = NoopLogger()) -> None:
        self._logger = logger
        self._itemno = 0

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        self._logger._log(message, severity, indent, prefix)

    def begin(self, ident: str | None = None, skipfailed: bool = False) -> PackageMaker:
        self._itemno += 1
        return PackageMaker(self._logger, ident, self._itemno, skipfailed)
