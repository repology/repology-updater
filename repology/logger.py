# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from abc import ABC, abstractmethod
from typing import ClassVar, List, Tuple


class Logger(ABC):
    NOTICE: ClassVar[int] = 1
    WARNING: ClassVar[int] = 2
    ERROR: ClassVar[int] = 3

    def log(self, message: str, severity: int = NOTICE) -> None:
        if severity == Logger.ERROR:
            message = 'ERROR: ' + message
        if severity == Logger.WARNING:
            message = 'WARNING: ' + message

        self._write_log(message, severity)

    def get_prefixed(self, prefix: str) -> 'Logger':
        return LoggerProxy(self, prefix=prefix)

    def get_indented(self, indent: int = 1) -> 'Logger':
        return LoggerProxy(self, indent=indent)

    @abstractmethod
    def _write_log(self, message: str, severity: int) -> None:
        pass

    # XXX: compatibility shim
    def Log(self, message: str) -> None:
        self.log(message, severity=Logger.NOTICE)


class LoggerProxy(Logger):
    _parent: Logger
    _prefix: str
    _indent: int

    def __init__(self, parent: Logger, prefix: str = '', indent: int = 0) -> None:
        if isinstance(parent, LoggerProxy):
            self._parent = parent._parent
            self._prefix = parent._prefix + prefix
            self._indent = parent._indent + indent
        else:
            self._parent = parent
            self._prefix = prefix
            self._indent = indent

    def _write_log(self, message: str, severity: int) -> None:
        self._parent._write_log(self._prefix + '  ' * self._indent + message, severity)


class NoopLogger(Logger):
    def _write_log(self, message: str, severity: int) -> None:
        pass


class FileLogger(Logger):
    def __init__(self, path: str) -> None:
        self.path = path

    def _write_log(self, message: str, severity: int) -> None:
        with open(self.path, 'a', encoding='utf-8') as logfile:
            fcntl.flock(logfile, fcntl.LOCK_EX)
            print(time.strftime('%b %d %T ') + message, file=logfile)


class FastFileLogger(Logger):
    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self):
        self.fd = open(self.path, 'a', encoding='utf-8')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.close()

    def _write_log(self, message: str, severity: int) -> None:
        print(time.strftime('%b %d %T ') + message, file=self.fd)


class StderrLogger(Logger):
    def _write_log(self, message, severity):
        print(time.strftime('%b %d %T ') + message, file=sys.stderr)


class AccumulatingLogger(Logger):
    def __init__(self) -> None:
        self.entries: List[Tuple[str, int]] = []

    def _write_log(self, message: str, severity: int) -> None:
        self.entries.append((message, severity))

    def get(self) -> List[Tuple[str, int]]:
        return self.entries

    def forward(self, otherlogger: Logger) -> None:
        for message, severity in self.entries:
            otherlogger.log(message, severity)
