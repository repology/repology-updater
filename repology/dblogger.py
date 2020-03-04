# Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import resource
import traceback
from typing import Any, List, Optional, Tuple

from repology.database import Database
from repology.logger import Logger, format_log_entry


def _severity_to_sql(severity: int) -> str:
    if severity == Logger.NOTICE:
        return 'notice'
    elif severity == Logger.WARNING:
        return 'warning'
    elif severity == Logger.ERROR:
        return 'error'
    else:
        raise RuntimeError('Unknown severity ' + str(severity))


class RealtimeDatabaseLogger(Logger):
    _db: Database
    _run_id: int
    _numlines: int
    _maxlines: int

    def __init__(self, db: Database, run_id: int, maxlines: int = 2500) -> None:
        self._db = db
        self._run_id = run_id
        self._numlines = 0
        self._maxlines = maxlines

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        if self._numlines == self._maxlines:
            self._db.add_log_line(
                self._run_id,
                self._numlines + 1,
                None,
                _severity_to_sql(Logger.ERROR),
                'Log trimmed at {} lines'.format(self._maxlines)
            )
            self._numlines += 1

        if self._numlines >= self._maxlines:
            return

        self._db.add_log_line(
            self._run_id,
            self._numlines + 1,
            None,
            _severity_to_sql(severity),
            format_log_entry(message, severity, indent, prefix)
        )
        self._numlines += 1


class PostponedDatabaseLogger(Logger):
    _lines: List[Tuple[datetime.datetime, str, int]]
    _maxlines: int

    def __init__(self, maxlines: int = 2500) -> None:
        self._lines = []
        self._maxlines = maxlines

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        if len(self._lines) == self._maxlines:
            self._lines.append((
                datetime.datetime.now(),
                'Log trimmed at {} lines'.format(self._maxlines),
                Logger.ERROR
            ))

        if len(self._lines) >= self._maxlines:
            return

        self._lines.append((
            datetime.datetime.now(),
            format_log_entry(message, severity, indent, prefix),
            severity
        ))

    def flush(self, db: Database, run_id: int) -> None:
        for lineno, (timestamp, formatted_message, severity) in enumerate(self._lines, 1):
            db.add_log_line(
                run_id,
                lineno,
                timestamp,
                _severity_to_sql(severity),
                formatted_message
            )


class RunHandler(Logger):
    _db: Database
    _run_id: int
    _start_rusage: Any
    _logger: Logger
    _no_changes: bool = False
    _num_lines: int = 0
    _num_warnings: int = 0
    _num_errors: int = 0

    def __init__(self, db: Database, reponame: str, run_type: str) -> None:
        self._db = db
        self._run_id = self._db.start_run(reponame, run_type)
        self._start_rusage = resource.getrusage(resource.RUSAGE_SELF)
        self._logger = RealtimeDatabaseLogger(self._db, self._run_id)

    def _log(self, message: str, severity: int, indent: int, prefix: str) -> None:
        self._logger._log(message, severity, indent, prefix)
        self._num_lines += 1
        if severity == Logger.WARNING:
            self._num_warnings += 1
        if severity == Logger.ERROR:
            self._num_errors += 1

    def set_no_changes(self) -> None:
        self._no_changes = True

    def finish(self, status: str = 'successful', traceback_text: Optional[str] = None) -> None:
        end_rusage = resource.getrusage(resource.RUSAGE_SELF)

        self._db.finish_run(
            id=self._run_id,
            status=status,
            num_lines=self._num_lines,
            num_warnings=self._num_warnings,
            num_errors=self._num_errors,
            no_changes=self._no_changes,
            utime=datetime.timedelta(seconds=end_rusage.ru_utime - self._start_rusage.ru_utime),
            stime=datetime.timedelta(seconds=end_rusage.ru_stime - self._start_rusage.ru_stime),
            maxrss=end_rusage.ru_maxrss,
            maxrss_delta=end_rusage.ru_maxrss - self._start_rusage.ru_maxrss,
            traceback=traceback_text
        )


class LogRunManager:
    _db: Database
    _reponame: str
    _run_type: str
    _run: RunHandler

    # XXX: move everything into RunHandler
    def __init__(self, db: Database, reponame: str, run_type: str):
        self._db = db
        self._reponame = reponame
        self._run_type = run_type

    def __enter__(self) -> RunHandler:
        self._run = RunHandler(self._db, self._reponame, self._run_type)

        return self._run

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        traceback_text = None

        status = 'successful'

        if exc_type is KeyboardInterrupt:
            self._run.log('interrupted by administrator', severity=Logger.WARNING)
            status = 'interrupted'
        elif exc_type:
            self._run.log('{}: {}'.format(exc_type.__name__, exc_val), severity=Logger.ERROR)
            status = 'failed'
            traceback_text = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))

        self._run.finish(status, traceback_text)
