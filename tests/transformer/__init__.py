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

from collections import defaultdict

from repology.repomgr import RepositoryManager
from repology.transformer import PackageTransformer
from repology.transformer.ruleset import Ruleset

from ..package import PackageSample


_repomgr = RepositoryManager(repostext="""
[
    { name: dummyrepo, desc: dummyrepo, family: dummyrepo, sources: [] },
    { name: foo, desc: foo, family: foo, sources: [] },
    { name: bar, desc: bar, family: bar, sources: [] },
    { name: baz, desc: baz, family: baz, sources: [] }
]
""")


def check_transformer(rulestext: str, *samples: PackageSample) -> None:
    __tracebackhide__ = True

    ruleset = Ruleset(rulestext=rulestext)

    sample_by_repo = defaultdict(list)

    for sample in samples:
        sample_by_repo[sample.package.repo].append(sample)

    for repo, repo_samples in sample_by_repo.items():
        transformer = PackageTransformer(ruleset, repo, {repo})
        for sample in repo_samples:
            transformer.process(sample.package)
            sample.check_pytest()
