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
-- !!update_link_status(url, status, redirect=None, size=None, location=None)
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


--------------------------------------------------------------------------------
--
-- !!get_links_for_check(after=None, prefix=None, recheck_age=None, limit=None, unchecked_only=False, checked_only=False, failed_only=False, succeeded_only=False) -> array of values
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


--------------------------------------------------------------------------------
--
-- !!get_metapackage_link_statuses(effname) -> dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	url,
	last_checked,
	last_success,
	last_failure,
	status,
	redirect,
	size,
	location
FROM links
WHERE url in (
	-- this additional wrap seem to fix query planner somehow
	-- to use index scan on links instead of seq scan, which
	-- makes the query 100x faster; XXX: recheck with postgres 10
	-- or report this?
	SELECT DISTINCT
		url
	FROM (
		SELECT
			unnest(downloads) AS url
		FROM packages
		WHERE effname = %(effname)s
		UNION
		SELECT
			homepage AS url
		FROM packages
		WHERE homepage IS NOT NULL AND effname = %(effname)s
	) AS tmp
);
