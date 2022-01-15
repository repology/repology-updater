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
from typing import Any, ClassVar


def format_log_entry(message: str, severity: int, indent: int, prefix: str) -> str:
    return prefix + '  ' * indent + message


class Logger(ABC):
    NOTICE: ClassVar[int] = 1
    WARNING: ClassVar[int] = 2
    ERROR: ClassVar[int] = 3

    def log(self, message: str, severity: int = NOTICE, indent: int = 0, prefix: str = '') -> None:
        if severity == Logger.ERROR:
            message = 'ERROR: ' + message
        elif severity == Logger.WARNING:
            message = 'WARNING: ' + message

        self._log(message, severity, indent, prefix)

    @abstractmethod
    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        pass

    def get_indented(self, indent: int = 1) -> 'Logger':
        return LoggerProxy(self, indent=indent)

    def get_prefixed(self, prefix: str) -> 'Logger':
        return LoggerProxy(self, prefix=prefix)


class LoggerProxy(Logger):
    _parent: Logger
    _indent: int
    _prefix: str

    def __init__(self, parent: Logger, indent: int = 0, prefix: str = '') -> None:
        self._parent = parent
        self._indent = indent
        self._prefix = prefix

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        self._parent._log(message, severity, indent + self._indent, self._prefix + prefix)


class NoopLogger(Logger):
    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        pass


class FileLogger(Logger):
    def __init__(self, path: str) -> None:
        self.path = path

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        with open(self.path, 'a', encoding='utf-8') as logfile:
            fcntl.flock(logfile, fcntl.LOCK_EX)
            print(time.strftime('%b %d %T ') + format_log_entry(message, severity, indent, prefix), file=logfile)


class FastFileLogger(Logger):
    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self) -> None:
        self.fd = open(self.path, 'a', encoding='utf-8')

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.fd.close()

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        print(time.strftime('%b %d %T ') + format_log_entry(message, severity, indent, prefix), file=self.fd)


class StderrLogger(Logger):
    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        print(time.strftime('%b %d %T ') + format_log_entry(message, severity, indent, prefix), file=sys.stderr)


class AccumulatingLogger(Logger):
    _entries: list[tuple[str, int, int, str]]

    def __init__(self) -> None:
        self._entries = []

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        self._entries.append((message, severity, indent, prefix))

    def get(self) -> list[str]:
        return [format_log_entry(*args) for args in self._entries]

    def forward(self, otherlogger: Logger) -> None:
        for args in self._entries:
            otherlogger._log(*args)
