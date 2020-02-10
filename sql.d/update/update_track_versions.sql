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
WITH old AS (
	SELECT
		(SELECT id FROM repositories WHERE repositories.name = repo) AS repository_id,
		trackname,
		version,
		count(*) AS refcount
	FROM packages
	WHERE effname IN (SELECT effname FROM changed_projects)
	GROUP BY repo, trackname, version
), new AS (
	SELECT
		(SELECT id FROM repositories WHERE repositories.name = repo) AS repository_id,
		trackname,
		version,
		count(*) AS refcount,
		bit_or(1 << versionclass) AS any_statuses,
		bit_or(flags) AS any_flags
	FROM incoming_packages
	GROUP BY repo, trackname, version
), delta AS (
	SELECT
		repository_id,
		trackname,
		version,
		coalesce(new.refcount, 0) - coalesce(old.refcount, 0) AS delta_refcount,
		coalesce(any_statuses, 0) AS any_statuses,
		coalesce(any_flags, 0) AS any_flags
	FROM old FULL OUTER JOIN new USING(repository_id, trackname, version)
)
INSERT INTO repo_track_versions (
	repository_id,
	trackname,
	version,
	any_statuses,
	any_flags,
	refcount
)
SELECT
	repository_id,
	trackname,
	version,
	any_statuses,
	any_flags,
	delta_refcount
FROM delta
ON CONFLICT (repository_id, trackname, version)
DO UPDATE SET
	any_statuses = repo_track_versions.any_statuses | EXCLUDED.any_statuses,
	any_flags = repo_track_versions.any_flags | EXCLUDED.any_flags,
	refcount = repo_track_versions.refcount + EXCLUDED.refcount,
	end_ts = CASE WHEN repo_track_versions.refcount + EXCLUDED.refcount = 0 THEN now() ELSE NULL END
WHERE
	repo_track_versions.any_statuses != EXCLUDED.any_statuses OR
	repo_track_versions.any_flags != EXCLUDED.any_flags OR
	EXCLUDED.refcount != 0;

{% if analyze %}
ANALYZE repo_track_versions;
{% endif %}
