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
-- @param after=None
-- @param prefix=None
-- @param recheck_age=None
-- @param limit=None
-- @param unchecked_only=False
-- @param checked_only=False
-- @param failed_only=False
-- @param succeeded_only=False
--
-- @returns array of values
--
--------------------------------------------------------------------------------
SELECT
	url
FROM links
WHERE
	(
		-- we are currently only able to check HTTP(s) urls
		url LIKE 'https://%%' OR
		url LIKE 'http://%%'
	) AND (
		-- pagination condition
		%(after)s IS NULL OR
		url > %(after)s
	) AND (
		-- prefix condition
		%(prefix)s IS NULL OR
		url LIKE (%(prefix)s || '%%')
	) AND (
		-- age condition
		%(recheck_age)s IS NULL OR
		last_checked IS NULL OR
		last_checked <= now() - INTERVAL %(recheck_age)s
	) AND (
		-- boolean expressions
		NOT %(unchecked_only)s OR
		last_checked IS NULL
	) AND (
		NOT %(checked_only)s OR
		last_checked IS NOT NULL
	) AND (
		NOT %(failed_only)s OR
		status != 200
	) AND (
		NOT %(succeeded_only)s OR
		status = 200
	)
ORDER BY url
LIMIT %(limit)s;
