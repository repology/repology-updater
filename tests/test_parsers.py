# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json

from repology.config import config
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor


def test_parsers_regress(regtest):
    repomgr = RepositoryManager(config['REPOS_DIR'])
    repoproc = RepositoryProcessor(repomgr, 'testdata', 'testdata', safety_checks=False)

    # NOTE: run the following command to canonize this test after parser or testdata update
    #
    #     pytest -k test_parsers_regress --regtest-reset
    #
    with regtest:
        for package in repoproc.iter_parse(reponames=['have_testdata']):
            print(json.dumps(package.__dict__, indent=1))
