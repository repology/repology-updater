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

from repology.logger import Logger


def _severity_to_sql(severity):
    if severity == Logger.NOTICE:
        return 'notice'
    elif severity == Logger.WARNING:
        return 'warning'
    elif severity == Logger.ERROR:
        return 'error'
    else:
        raise RuntimeError('Unknown severity ' + str(severity))


class RealtimeDatabaseLogger(Logger):
    def __init__(self, db, run_id, maxlines=2500):
        self.db = db
        self.run_id = run_id
        self.numlines = 0
        self.maxlines = maxlines

    def _write_log(self, message, severity):
        if self.numlines == self.maxlines:
            self.db.add_log_line(
                self.run_id,
                self.numlines + 1,
                None,
                _severity_to_sql(Logger.ERROR),
                'Log trimmed at {} lines'.format(self.maxlines)
            )
            self.numlines += 1

        if self.numlines >= self.maxlines:
            return

        self.db.add_log_line(
            self.run_id,
            self.numlines + 1,
            None,
            _severity_to_sql(severity),
            message
        )
        self.numlines += 1


class PostponedDatabaseLogger(Logger):
    def __init__(self, maxlines=2500):
        self.lines = []
        self.maxlines = maxlines

    def _write_log(self, message, severity):
        if len(self.lines) == self.maxlines:
            self.lines.append((
                datetime.datetime.now(),
                Logger.ERROR,
                'Log trimmed at {} lines'.format(self.maxlines)
            ))

        if len(self.lines) >= self.maxlines:
            return

        self.lines.append((
            datetime.datetime.now(),
            severity,
            message
        ))

    def flush(self, db, run_id):
        for lineno, (timestamp, severity, message) in enumerate(self.lines, 1):
            self.db.add_log_line(
                run_id,
                lineno,
                timestamp,
                _severity_to_sql(severity),
                message
            )


class LogRunManager:
    def __init__(self, db, reponame, run_type):
        self.db = db
        self.reponame = reponame
        self.run_type = run_type

    def __enter__(self):
        self.run_id = self.db.start_run(self.reponame, self.run_type)
        self.logger = RealtimeDatabaseLogger(self.db, self.run_id)

        self.db.update_repository_run_id(self.reponame, self.run_id, 'current')

        self.start_rusage = resource.getrusage(resource.RUSAGE_SELF)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_rusage = resource.getrusage(resource.RUSAGE_SELF)

        success = True
        trace = None

        if exc_type is KeyboardInterrupt:
            self.db.update_repository_run_id(self.reponame, None, 'current')
            return

        if exc_type:
            self.logger.log('{}: {}'.format(exc_type.__name__, exc_val), severity=Logger.ERROR)
            success = False
            trace = traceback.format_exception(exc_type, exc_val, exc_tb)

        self.db.finish_run(
            self.run_id,
            success,
            utime=datetime.timedelta(seconds=end_rusage.ru_utime - self.start_rusage.ru_utime),
            stime=datetime.timedelta(seconds=end_rusage.ru_stime - self.start_rusage.ru_stime),
            maxrss=end_rusage.ru_maxrss,
            maxrss_delta=end_rusage.ru_maxrss - self.start_rusage.ru_maxrss,
            traceback=trace
        )

        self.db.update_repository_run_id(self.reponame, None, 'current')
        self.db.update_repository_run_id(self.reponame, self.run_id, self.run_type, success)
