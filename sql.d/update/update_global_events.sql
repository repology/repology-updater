-- Copyright (C) 2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

WITH old AS (
	SELECT
		effname,
		-- XXX: technical dept warning: since we don't distinguish "newest unique" and "devel unique" statuses, we have
		-- to use flags here. Better solution should be implemented in future
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
		) AS devel_versions,
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
		) AS newest_versions
	FROM old_packages
	WHERE NOT (flags & (32768 | 131072))::bool
	GROUP BY effname
), new AS (
	SELECT
		effname,
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
		) AS devel_versions,
		array_agg(DISTINCT repo ORDER BY repo) FILTER(
			WHERE
				(versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool))
				-- exclude ignored; these repos probably faked the update before
				-- and may still not be in fact on the latest version
				AND NOT (flags & (4 | 8 | 16))::bool
		) AS devel_repos,
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
		) AS newest_versions,
		array_agg(DISTINCT repo ORDER BY repo) FILTER(
			WHERE
				(versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool))
				AND NOT (flags & (4 | 8 | 16))::bool
		) AS newest_repos
	FROM incoming_packages
	WHERE NOT (flags & (32768 | 131072))::bool  -- ignore altscheme and altver, only support primary version for now
	GROUP BY effname
), diff AS (
	SELECT
		effname,

		-- XXX: these do NOT take alternative versions into account
		version_set_changed(old.devel_versions, new.devel_versions) AS is_devel_update,
		version_set_changed(old.newest_versions, new.newest_versions) AS is_newest_update,

		new.devel_versions AS devel_versions,
		new.newest_versions AS newest_versions,
		devel_repos,
		newest_repos
	FROM old RIGHT JOIN new USING(effname)
)
INSERT INTO global_version_events (
	effname,
	ts,
	type,
	spread,
	data
)
SELECT
	effname,
	now(),
	type,
	(SELECT num_families FROM metapackages WHERE metapackages.effname = events.effname),
	data
FROM (
	--------------------------------------------------------------------------------
	-- newest update
	--------------------------------------------------------------------------------
	SELECT
		effname,
		'newest_update'::global_version_event_type AS type,
		jsonb_strip_nulls(jsonb_build_object(
			'versions', newest_versions,
			'repos', newest_repos
		)) AS data
	FROM diff WHERE is_newest_update AND newest_versions IS NOT NULL
	--------------------------------------------------------------------------------
	-- devel update
	--------------------------------------------------------------------------------
	UNION ALL
	SELECT
		effname,
		'devel_update'::global_version_event_type AS type,
		jsonb_strip_nulls(jsonb_build_object(
			'versions', devel_versions,
			'repos', devel_repos
		)) AS data
	FROM diff WHERE is_devel_update AND devel_versions IS NOT NULL
) AS events;
