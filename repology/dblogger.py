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

import datetime
import resource
import traceback
from typing import Any, List, Tuple

from repology.database import Database
from repology.logger import Logger


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

    def _write_log(self, message: str, severity: int) -> None:
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
            message
        )
        self._numlines += 1


class PostponedDatabaseLogger(Logger):
    _lines: List[Tuple[datetime.datetime, int, str]]
    _maxlines: int

    def __init__(self, maxlines: int = 2500) -> None:
        self._lines = []
        self._maxlines = maxlines

    def _write_log(self, message: str, severity: int) -> None:
        if len(self._lines) == self._maxlines:
            self._lines.append((
                datetime.datetime.now(),
                Logger.ERROR,
                'Log trimmed at {} lines'.format(self._maxlines)
            ))

        if len(self._lines) >= self._maxlines:
            return

        self._lines.append((
            datetime.datetime.now(),
            severity,
            message
        ))

    def flush(self, db: Database, run_id: int) -> None:
        for lineno, (timestamp, severity, message) in enumerate(self._lines, 1):
            db.add_log_line(
                run_id,
                lineno,
                timestamp,
                _severity_to_sql(severity),
                message
            )


class LogRunManager:
    _db: Database
    _reponame: str
    _run_type: str
    _target_status: str
    _no_changes: bool
    _start_rusage: Any
    _logger: Logger

    def __init__(self, db: Database, reponame: str, run_type: str):
        self._db = db
        self._reponame = reponame
        self._run_type = run_type
        self._target_status = 'successful'
        self._no_changes = False

    def __enter__(self) -> Logger:
        self._run_id = self._db.start_run(self._reponame, self._run_type)
        self._start_rusage = resource.getrusage(resource.RUSAGE_SELF)
        self._logger = RealtimeDatabaseLogger(self._db, self._run_id)

        class HelperLogger(Logger):
            def _write_log(dummyself, message: str, severity: int = Logger.NOTICE) -> None:
                self._logger.log(message, severity)

            def _set_no_changes(dummyself) -> None:
                self._no_changes = True

        return HelperLogger()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        end_rusage = resource.getrusage(resource.RUSAGE_SELF)

        target_status = self._target_status
        trace = None

        if exc_type is KeyboardInterrupt:
            self._logger.log('interrupted by administrator', severity=Logger.WARNING)
            target_status = 'interrupted'
        elif exc_type:
            self._logger.log('{}: {}'.format(exc_type.__name__, exc_val), severity=Logger.ERROR)
            target_status = 'failed'
            trace = traceback.format_exception(exc_type, exc_val, exc_tb)

        self._db.finish_run(
            self._run_id,
            target_status,
            self._no_changes,
            utime=datetime.timedelta(seconds=end_rusage.ru_utime - self._start_rusage.ru_utime),
            stime=datetime.timedelta(seconds=end_rusage.ru_stime - self._start_rusage.ru_stime),
            maxrss=end_rusage.ru_maxrss,
            maxrss_delta=end_rusage.ru_maxrss - self._start_rusage.ru_maxrss,
            traceback=trace
        )
