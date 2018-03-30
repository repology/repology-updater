-- Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param url
-- @param status
-- @param redirect=None
-- @param size=None
-- @param location=None
--
--------------------------------------------------------------------------------
UPDATE links
SET
	last_checked = now(),
	last_success = CASE WHEN %(status)s = 200 THEN now() ELSE last_success END,
	last_failure = CASE WHEN %(status)s != 200 THEN now() ELSE last_failure END,
	status = %(status)s,
	redirect = %(redirect)s,
	size = %(size)s,
	location = %(location)s
WHERE url = %(url)s;
