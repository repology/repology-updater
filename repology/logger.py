# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import sys
import time


class Logger():
    NOTICE = 1
    WARNING = 2
    ERROR = 3

    def log(self, message, severity=NOTICE):
        if severity == Logger.ERROR:
            message = 'ERROR: ' + message
        if severity == Logger.WARNING:
            message = 'WARNING: ' + message

        self._write_log(message, severity)

    def get_prefixed(self, prefix):
        return LoggerProxy(self, prefix=prefix)

    def get_indented(self, indent=1):
        return LoggerProxy(self, indent=indent)

    def _write_log(self, message, severity):
        pass

    # XXX: compatibility shims
    def Log(self, message):
        return self.log(message, severity=Logger.NOTICE)

    def GetPrefixed(self, *args, **kwargs):
        return self.get_prefixed(*args, **kwargs)

    def GetIndented(self, *args, **kwargs):
        return self.get_indented(*args, **kwargs)


class LoggerProxy(Logger):
    def __init__(self, parent, prefix='', indent=0):
        if isinstance(parent, LoggerProxy):
            self.parent = parent.parent
            self.prefix = parent.prefix + prefix
            self.indent = parent.indent + indent
        else:
            self.parent = parent
            self.prefix = prefix
            self.indent = indent

    def _write_log(self, message, severity):
        self.parent._write_log(self.prefix + '  ' * self.indent + message, severity)


class NoopLogger(Logger):
    pass


class FileLogger(Logger):
    def __init__(self, path):
        self.path = path

    def _write_log(self, message, severity):
        with open(self.path, 'a', encoding='utf-8') as logfile:
            fcntl.flock(logfile, fcntl.LOCK_EX)
            print(time.strftime('%b %d %T ') + message, file=logfile)


class FastFileLogger(Logger):
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.fd = open(self.path, 'a', encoding='utf-8')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.close()

    def _write_log(self, message, severity):
        print(time.strftime('%b %d %T ') + message, file=self.fd)


class StderrLogger(Logger):
    def _write_log(self, message, severity):
        print(time.strftime('%b %d %T ') + message, file=sys.stderr)


class AccumulatingLogger(Logger):
    def __init__(self):
        self.entries = []

    def _write_log(self, message, severity):
        self.entries.append((message, severity))

    def get(self):
        return self.entries

    def forward(self, otherlogger):
        for message, severity in self.entries:
            otherlogger.log(message, severity)
