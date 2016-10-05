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

import fcntl
import time
import sys


class NoopLogger:
    def __init__(self):
        pass

    def Log(self, message):
        pass

    def GetPrefixed(self, prefix):
        return NoopLogger()


class FileLogger:
    def __init__(self, path, prefix=None):
        self.path = path
        self.prefix = prefix
        pass

    def Log(self, message):
        prefixstr = self.prefix if self.prefix else ""
        with open(self.path, "a") as logfile:
            fcntl.flock(logfile, fcntl.LOCK_EX)
            print(time.strftime("%b %d %T ") + prefixstr + message,
                  file=logfile)

    def GetPrefixed(self, prefix):
        return FileLogger(self.path,
                          self.prefix + prefix if self.prefix else prefix)


class StderrLogger:
    def __init__(self, prefix=None):
        self.prefix = prefix
        pass

    def Log(self, message):
        prefixstr = self.prefix if self.prefix else ""
        print(time.strftime("%b %d %T ") + prefixstr + message,
              file=sys.stderr)

    def GetPrefixed(self, prefix):
        return StderrLogger(self.prefix + prefix if self.prefix else prefix)
