from typing import Iterable

from repology.packagemaker import PackageFactory, PackageMaker, LinkType
from repology.parsers import Parser
from repology.parsers.json import iter_json_list


class SisyphusJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, ('packages', None)):
            with factory.begin() as pkg:
                pkg.add_name(packagedata['name'])
                pkg.set_version(packagedata['version'])
                pkg.set_rawversion(
                    f"{packagedata['epoch']}:{packagedata['version']}-{packagedata['release']}"
                )
                pkg.add_categories(packagedata['category'])
                pkg.add_homepages(packagedata['url'])
                pkg.set_summary(packagedata['summary'])
                pkg.add_licenses(packagedata['license'])
                pkg.add_maintainers(packagedata['packager'])
                # store package epoch and release
                pkg.set_extra_field('epoch', packagedata['epoch'])
                pkg.set_extra_field('release', packagedata['release'])
                # store source package binaries
                # XXX: is there any way to store binary packages extra fields?
                pkg.add_binnames(
                    [b['name'] for b in packagedata['binaries']]
                )
                # set package links
                pkg.add_links(LinkType.PACKAGE_HOMEPAGE, packagedata['homepage'])
                pkg.add_links(LinkType.PACKAGE_RECIPE_RAW, packagedata['recipe'])
                pkg.add_links(LinkType.PACKAGE_ISSUE_TRACKER, packagedata['bugzilla'])
                # TODO: parse CPE data when available
                if 'CPE' in packagedata:
                    pass

                yield pkg
