-- Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
--
-- This file is part of repology
--
-- repology is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- repology is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with repology.  If not, see <http://www.gnu.org/licenses/>.

--------------------------------------------------------------------------------
--
-- @param run_id
-- @param lineno
-- @param timestamp
-- @param severity
-- @param message
--
--------------------------------------------------------------------------------
INSERT INTO log_lines(
	run_id,
	lineno,

	timestamp,
	severity,
	message
)
VALUES (
	%(run_id)s,
	%(lineno)s,

{% if timestamp %}
	%(timestamp)s,
{% else %}
	now(),
{% endif %}

	%(severity)s,
	%(message)s
);
