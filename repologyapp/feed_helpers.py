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

import datetime
from typing import Any, Collection, Dict, Optional


def smear_timestamps(entries: Collection[Dict[str, Any]]) -> Collection[Dict[str, Any]]:
    prev_ts: Optional[datetime.datetime] = None

    for entry in entries:
        if 'ts' in entry and prev_ts and entry['ts'] >= prev_ts:
            entry['ts'] = prev_ts - datetime.timedelta(seconds=1)
        prev_ts = entry['ts']

    return entries
