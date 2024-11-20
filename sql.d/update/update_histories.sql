-- Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- History snapshot
--------------------------------------------------------------------------------

-- per-repository counters
WITH repositories_counters AS (
	SELECT
		name,
		num_metapackages,
		num_metapackages_unique,
		num_metapackages_newest,
		num_metapackages_outdated,
		num_metapackages_comparable,
		num_metapackages_problematic,
		num_problems,
		num_maintainers,
		num_metapackages_vulnerable
	FROM repositories
	WHERE state != 'legacy'
), snapshot_candidate AS (
	SELECT
		now() AS ts,
		jsonb_object_agg(repositories_counters.name, to_jsonb(repositories_counters) - 'name') AS snapshot
	FROM repositories_counters
)
INSERT INTO repositories_history (
	ts,
	snapshot
)
SELECT
	ts,
	snapshot
FROM snapshot_candidate
WHERE snapshot IS NOT NULL;

INSERT INTO repositories_history_new (
	repository_id,
	ts,
	num_problems,
	num_maintainers,
	num_projects,
	num_projects_unique,
	num_projects_newest,
	num_projects_outdated,
	num_projects_comparable,
	num_projects_problematic,
	num_projects_vulnerable
)
SELECT
	id,
	now(),
	num_problems,
	num_maintainers,
	num_metapackages,
	num_metapackages_unique,
	num_metapackages_newest,
	num_metapackages_outdated,
	num_metapackages_comparable,
	num_metapackages_problematic,
	num_metapackages_vulnerable
FROM repositories
WHERE state != 'legacy';

-- global statistics
INSERT INTO statistics_history (
	ts,
	snapshot
)
SELECT
	now(),
	to_jsonb(snapshot)
FROM (
	SELECT
		*
	FROM statistics
) AS snapshot;
