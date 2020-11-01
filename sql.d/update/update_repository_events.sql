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

WITH old AS (
	SELECT
		effname,
		repo,

		array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass IN (1, 4, 5)) AS versions_uptodate,
		array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 2) AS versions_outdated,
		array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass IN (3, 7, 8)) AS versions_ignored
	FROM old_packages
	GROUP BY effname,repo
), new AS (
	SELECT
		effname,
		repo,

		array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass IN (1, 4, 5)) AS versions_uptodate,
		array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 2) AS versions_outdated,
		array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass IN (3, 7, 8)) AS versions_ignored
	FROM incoming_packages
	GROUP BY effname,repo
), diff AS (
	SELECT
		(SELECT id FROM repositories WHERE name = coalesce(new.repo, old.repo)) AS repository_id,
		(SELECT id FROM metapackages WHERE effname = coalesce(new.effname, old.effname)) AS project_id,

		effname,

		old.effname IS NULL AS is_added,
		new.effname IS NULL AS is_removed,
		old.effname IS NOT NULL AND new.effname IS NOT NULL AS is_changed,

		(SELECT incomplete FROM repositories WHERE name = coalesce(new.repo, old.repo)) AS incomplete,

		old.versions_uptodate AS old_versions_uptodate,
		old.versions_outdated AS old_versions_outdated,
		old.versions_ignored AS old_versions_ignored,

		new.versions_uptodate AS new_versions_uptodate,
		new.versions_outdated AS new_versions_outdated,
		new.versions_ignored AS new_versions_ignored
	FROM old FULL OUTER JOIN new USING(effname,repo)
	WHERE (SELECT state FROM repositories WHERE name = coalesce(new.repo, old.repo)) = 'active'::repository_state
)
INSERT INTO repository_events (
	repository_id, metapackage_id, ts,
	type,
	data
)
--------------------------------------------------------------------------------
-- removed
--------------------------------------------------------------------------------
SELECT
	repository_id, project_id, now(),
	'removed'::maintainer_repo_metapackages_event_type,
	'{}'::jsonb
FROM diff
WHERE is_removed AND NOT incomplete
--------------------------------------------------------------------------------
-- added
--------------------------------------------------------------------------------
UNION ALL
SELECT
	repository_id, project_id, now(),
	'added'::maintainer_repo_metapackages_event_type,
	'{}'::jsonb
FROM diff
WHERE is_added AND NOT incomplete
--------------------------------------------------------------------------------
-- updates
--------------------------------------------------------------------------------
UNION ALL
SELECT
	repository_id, project_id, now(),
	'uptodate'::maintainer_repo_metapackages_event_type,
	jsonb_build_object('version', new_versions_uptodate[1])
FROM diff
WHERE new_versions_uptodate IS NOT NULL AND (is_added OR old_versions_uptodate[1] IS DISTINCT FROM new_versions_uptodate[1])
UNION ALL
SELECT
	repository_id, project_id, now(),
	'outdated'::maintainer_repo_metapackages_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'version', new_versions_outdated[1],
		'newest_versions', (
			SELECT
				array_agg(DISTINCT version ORDER BY version) FILTER(
					WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
				) ||
				array_agg(DISTINCT version ORDER BY version) FILTER(
					WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
				)
			FROM incoming_packages
			WHERE incoming_packages.effname = diff.effname
		)
	))
FROM diff
WHERE new_versions_outdated IS NOT NULL AND (is_added OR old_versions_outdated[1] IS DISTINCT FROM new_versions_outdated[1])
UNION ALL
SELECT
	repository_id, project_id, now(),
	'ignored'::maintainer_repo_metapackages_event_type,
	jsonb_build_object('version', new_versions_ignored[1])
FROM diff
WHERE new_versions_ignored IS NOT NULL AND (is_added OR old_versions_ignored[1] IS DISTINCT FROM new_versions_ignored[1])
;
