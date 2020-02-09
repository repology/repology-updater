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
-- @param partial=False
-- @param analyze=True
--------------------------------------------------------------------------------
DELETE FROM project_releases WHERE effname IN (SELECT effname FROM changed_projects);

WITH tracknames AS (
	SELECT DISTINCT
		effname,
		(SELECT id FROM repositories WHERE name=incoming_packages.repo) AS repository_id,
		trackname
	FROM incoming_packages
)
INSERT INTO project_releases (
	effname,
	version,
	trusted,
	start_ts,
	trusted_start_ts,
	end_ts
)
SELECT
	effname,
	version,
	NOT is_ignored_by_masks(bit_or(any_statuses), bit_and(any_flags)),
	min(start_ts),
	min(start_ts) FILTER (WHERE NOT is_ignored_by_masks(any_statuses, any_flags)),
	max(end_ts)
FROM tracknames INNER JOIN repo_track_versions USING(repository_id, trackname)
GROUP BY effname, version;

{% if analyze %}
ANALYZE project_releases;
{% endif %}
