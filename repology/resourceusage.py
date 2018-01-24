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

import resource


class ResourceUsageMonitor:
    def __init__(self):
        self.start_usage = resource.getrusage(resource.RUSAGE_SELF)

    def Get(self, restart=False):
        """Get difference of start and current usage.

        See https://docs.python.org/3/library/resource.html for field descriptions
        """
        start_usage = self.start_usage
        current_usage = resource.getrusage(resource.RUSAGE_SELF)

        if restart:
            self.start_usage = current_usage

        return list(
            map(lambda pair: pair[1] - pair[0], zip(start_usage, current_usage))
        )

    def GetStr(self, restart=False):
        usage = self.Get(restart)

        return '{:.2f}s user, {:.2f}s system, {:+.2f}MB rss'.format(usage[0], usage[1], usage[2] / 1024.0)
