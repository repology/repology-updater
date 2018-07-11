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

    def get_usage_data(self, restart=False):
        """Get difference of start and current usage.

        See https://docs.python.org/3/library/resource.html for field descriptions
        """
        current_usage = resource.getrusage(resource.RUSAGE_SELF)

        if restart:
            self.start_usage = current_usage

        return (
            current_usage.ru_utime - self.start_usage.ru_utime,
            current_usage.ru_stime - self.start_usage.ru_stime,
            current_usage.ru_maxrss - self.start_usage.ru_maxrss,
            current_usage.ru_maxrss
        )

    def get_usage_str(self, restart=False):
        usage = self.get_usage_data(restart)

        return '{:.2f}s user, {:.2f}s system, {:+.2f}MB rss to {:.2f}MB'.format(usage[0], usage[1], usage[2] / 1024.0, usage[3] / 1024.0)
