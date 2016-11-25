#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
import sys
import re
from argparse import ArgumentParser
from xml.sax.saxutils import escape
import shutil

from repology.package import *
from repology.nametransformer import NameTransformer
from repology.report import ReportProducer
from repology.template import Template
from repology.repoman import RepositoryManager
from repology.logger import *


def FilterPackages(metapackages, maintainer=None, category=None, manyrepos=None, littlerepos=None, inrepo=None, notinrepo=None, outdatedinrepo=None):
    filtered = []

    for metapackage in metapackages:
        if maintainer is not None and not metapackage.HasMaintainer(maintainer):
            continue

        if category is not None and not metapackage.HasCategoryLike(category):
            continue

        if manyrepos is not None and len(metapackage.GetFamilies()) < manyrepos:
            continue

        if littlerepos is not None and metapackage.GetNumRepos() > littlerepos:
            continue

        if inrepo is not None and not metapackage.HasRepository(inrepo):
            continue

        if notinrepo is not None and metapackage.HasRepository(notinrepo):
            continue

        if outdatedinrepo is not None and not metapackage.IsOutdatedInRepository(outdatedinrepo):
            continue

        filtered.append(metapackage)

    return filtered


def GenStatistics(metapackages, reponames):
    statistics = {
        reponame: {
            'total': 0,
            'good': 0,
            'bad': 0,
            'orphan': 0,
            'ignore': 0,
            'multi': 0,
            'lonely': 0,
        } for reponame in reponames}

    for metapackage in metapackages:
        for reponame, versiondata in metapackage.versions.items():
            statistics[reponame]['total'] += 1
            statistics[reponame][versiondata['class']] += 1

    # merge multi into good and add known
    for repodata in statistics.values():
        repodata['good'] = repodata['good'] + repodata['multi']
        del repodata['multi']
        repodata['known'] = repodata['good'] + repodata['bad']

    statistics['total'] = len(metapackages)

    return statistics


def RepologyOrg(path, metapackages, reponames, repometadata, logger):
    if not os.path.isdir(path):
        os.mkdir(path)

    template = Template()
    rp = ReportProducer(template, "table.html")

    logger.Log("===> Basic stuff")
    template.RenderToFile(
        'about.html',
        os.path.join(path, "about.html"),
        site_root="",
        subheader="About",
        subsection="about"
    )

    template.RenderToFile(
        'news.html',
        os.path.join(path, "news.html"),
        site_root="",
        subheader="News",
        subsection="news"
    )

    shutil.rmtree(os.path.join(path, "assets"), ignore_errors=True)
    shutil.copytree("assets", os.path.join(path, "assets"))

    logger.Log("===> Statistics")
    template.RenderToFile(
        'statistics.html',
        os.path.join(path, "statistics.html"),
        site_root="",
        reponames=reponames,
        repositories=repometadata,
        subheader="Statistics",
        subsection="statistics",
        statistics=GenStatistics(metapackages, reponames)
    )

    logger.Log("===> Main index")
    rp.RenderFilesPaginated(
        os.path.join(path, "index"),
        metapackages,
        reponames,
        500,
        repositories=repometadata,
        site_root="",
        subheader="Package index",
        subsection="packages"
    )

    shutil.copyfile(os.path.join(path, "index.0.html"), os.path.join(path, "index.html"))

    logger.Log("===> Specific sets")
    widespread_path = os.path.join(path, "widespread")
    if not os.path.isdir(widespread_path):
        os.mkdir(widespread_path)

    manyrepos = len(set([repometadata[repo]['family'] for repo in reponames])) - 2
    rp.RenderFilesPaginated(
        os.path.join(widespread_path, "widespread"),
        FilterPackages(metapackages, manyrepos=manyrepos),
        reponames,
        500,
        repositories=repometadata,
        site_root="../",
        subheader="Most wide-spread packages",
        subsection="widespread",
    )

    unique_path = os.path.join(path, "unique")
    if not os.path.isdir(unique_path):
        os.mkdir(unique_path)

    rp.RenderFilesPaginated(
        os.path.join(unique_path, "unique"),
        FilterPackages(metapackages, littlerepos=1),
        reponames,
        500,
        repositories=repometadata,
        site_root="../",
        subheader="Unique packages",
        subsection="unique",
    )

    logger.Log("===> Per-repository pages")
    inrepo_path = os.path.join(path, "repositories")
    if not os.path.isdir(inrepo_path):
        os.mkdir(inrepo_path)

    notinrepo_path = os.path.join(path, "missing")
    if not os.path.isdir(notinrepo_path):
        os.mkdir(notinrepo_path)

    outdatedinrepo_path = os.path.join(path, "outdated")
    if not os.path.isdir(outdatedinrepo_path):
        os.mkdir(outdatedinrepo_path)

    for repository in reponames:
        inrepo_packages = FilterPackages(metapackages, inrepo=repository)
        notinrepo_packages = FilterPackages(metapackages, notinrepo=repository, manyrepos=2)
        outdatedinrepo_packages = FilterPackages(metapackages, outdatedinrepo=repository)

        rp.RenderFilesPaginated(
            os.path.join(inrepo_path, repository),
            inrepo_packages,
            reponames,
            500,
            repositories=repometadata,
            site_root="../",
            subheader="Packages in " + repometadata[repository]['desc'],
            subsection="repositories"
        )

        rp.RenderFilesPaginated(
            os.path.join(notinrepo_path, repository),
            notinrepo_packages,
            reponames,
            500,
            repositories=repometadata,
            site_root="../",
            subheader="Packages missing from " + repometadata[repository]['desc'],
            subsection="missing"
        )

        rp.RenderFilesPaginated(
            os.path.join(outdatedinrepo_path, repository),
            outdatedinrepo_packages,
            reponames,
            500,
            repositories=repometadata,
            site_root="../",
            subheader="Packages outdated in " + repometadata[repository]['desc'],
            subsection="outdated"
        )

    template.RenderToFile(
        'repositories.html',
        os.path.join(inrepo_path, "index.html"),
        site_root="../",
        reponames=reponames,
        repositories=repometadata,
        subheader="Repositories",
        subsection="repositories",
        description='''
            For each repository, this section only lists packages it contains.
        '''
    )

    template.RenderToFile(
        'repositories.html',
        os.path.join(notinrepo_path, "index.html"),
        site_root="../",
        reponames=reponames,
        repositories=repometadata,
        subheader="Repositories with missing packages",
        subsection="missing",
        description='''
            For each repository, this section lists packages not present in it, but present in two other repositories.
        '''
    )

    template.RenderToFile(
        'repositories.html',
        os.path.join(outdatedinrepo_path, "index.html"),
        site_root="../",
        reponames=reponames,
        repositories=repometadata,
        subheader="Repositories with outdated packages",
        subsection="outdated",
    )

    logger.Log("===> Per-maintainer index")
    maintainers = {}
    for metapackage in metapackages:
        for maintainer in metapackage.GetMaintainers():
            if maintainer not in maintainers:
                maintainers[maintainer] = {
                    'sanitized_name': re.sub("[^a-zA-Z@.0-9]", "_", maintainer).lower(),
                    'num_packages': 0,
                    'packages': [],
                }

            # XXX: doesn't count multiple packages with same name
            maintainers[maintainer]['num_packages'] += 1
            maintainers[maintainer]['packages'].append(metapackage)

    maintainers_path = os.path.join(path, "maintainers")
    if not os.path.isdir(maintainers_path):
        os.mkdir(maintainers_path)

    for maintainer, maintainer_data in maintainers.items():
        maint_packages = maintainer_data['packages']

        rp.RenderFilesPaginated(
            os.path.join(maintainers_path, maintainer_data['sanitized_name']),
            maint_packages,
            reponames,
            500,
            repositories=repometadata,
            site_root="../",
            subheader="Packages maintained by " + escape(maintainer),
            subsection="maintainers"
        )

    template.RenderToFile(
        'maintainers.html',
        os.path.join(maintainers_path, "index.html"),
        site_root="../",
        maintainers=[
            {
                "fullname": escape(maintainer),
                "sanitizedname": maintainers[maintainer]['sanitized_name'],
                "num_packages": maintainers[maintainer]['num_packages'],
            } for maintainer in sorted(maintainers.keys())
        ],
        subheader="Package maintainers",
        subsection="maintainers"
    )

    logger.Log("===> Per-package pages")
    packages_path = os.path.join(path, "package")
    if not os.path.isdir(packages_path):
        os.mkdir(packages_path)

    for metapackage in metapackages:
        template.RenderToFile(
            'package.html',
            os.path.join(packages_path, metapackage.GetName() + ".html"),
            site_root="../",
            reponames=reponames,
            repositories=repometadata,
            subheader="Package {}".format(metapackage.GetName()),
            metapackage=metapackage,
            subsection="packages",
        )

    logger.Log("===> Site generation complete")

def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', help='path to directory with repository state')
    parser.add_argument('-U', '--rules', default='rules.yaml', help='path to name transformation rules yaml')
    parser.add_argument('-l', '--logfile', help='path to log file')

    parser.add_argument('-r', '--repository', action='append', help='specify repository names or tags to process')
    parser.add_argument('-S', '--no-shadow', action='store_true', help='treat shadow repositories as normal')

    parser.add_argument('-o', '--output', help='path to output directory')
    options = parser.parse_args()

    if not options.statedir:
        raise RuntimeError("please set --statedir")

    if not options.repository:
        options.repository = ["all"]

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    nametrans = NameTransformer(options.rules)
    repoman = RepositoryManager(options.statedir, enable_shadow=not options.no_shadow)
    packages = repoman.Deserialize(
        nametrans,
        reponames=options.repository,
        logger=logger
    )

    RepologyOrg(options.output, packages, repoman.GetNames(reponames=options.repository), repoman.GetMetadata(), logger)

    unmatched = nametrans.GetUnmatchedRules()
    if len(unmatched):
        wlogger = logger.GetPrefixed("WARNING: ")
        wlogger.Log("unmatched rules detected!")

        for rule in unmatched:
            wlogger.Log(rule)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
