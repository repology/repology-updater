-- Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param analyze=True
--------------------------------------------------------------------------------
WITH tracknames AS (
	SELECT DISTINCT
		effname,
		(SELECT id FROM repositories WHERE name=incoming_packages.repo) AS repository_id,
		trackname
	FROM incoming_packages
), incoming_releases AS (
	SELECT
		effname,
		version,
		min(start_ts) AS start_ts,
		min(start_ts) FILTER (WHERE NOT is_ignored_by_masks(any_statuses, any_flags)) AS trusted_start_ts,
		max(end_ts) AS end_ts,
		array_agg(DISTINCT start_ts) FILTER (WHERE is_ignored_by_masks(any_statuses, any_flags)) AS ignored_start_tses,
		array_agg(DISTINCT start_ts) FILTER (WHERE NOT is_ignored_by_masks(any_statuses, any_flags)) AS unignored_start_tses
	FROM tracknames INNER JOIN repo_track_versions USING(repository_id, trackname)
	GROUP BY effname, version
), new AS (
	INSERT INTO project_releases (
		effname,
		version,
		start_ts,
		trusted_start_ts,
		end_ts
	)
	SELECT
		effname,
		version,
		start_ts,
		trusted_start_ts,
		end_ts
	FROM incoming_releases
	ON CONFLICT DO NOTHING
)
UPDATE project_releases
SET
	start_ts = least(project_releases.start_ts, incoming_releases.start_ts),
	trusted_start_ts =
		-- Force reset trusted_start_ts if it's current value is among ignored ones
		CASE
			WHEN
				project_releases.trusted_start_ts = ANY(incoming_releases.ignored_start_tses)
				AND NOT coalesce(project_releases.trusted_start_ts = ANY(incoming_releases.unignored_start_tses), false)
			THEN incoming_releases.trusted_start_ts
			ELSE least(project_releases.trusted_start_ts, incoming_releases.trusted_start_ts)
		END,
	end_ts = greatest(project_releases.end_ts, incoming_releases.end_ts)
FROM incoming_releases
WHERE
	project_releases.effname = incoming_releases.effname AND
	project_releases.version = incoming_releases.version;

{% if analyze %}
ANALYZE project_releases;
{% endif %}
