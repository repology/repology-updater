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
-- @param effname
--
-- @returns dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	url,
	last_checked,
	ipv4_success,
	ipv4_permanent_redirect_target,
	ipv6_success,
	ipv6_permanent_redirect_target
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
) AND (
	ipv4_success IS NOT NULL OR
	ipv6_success IS NOT NULL
);
