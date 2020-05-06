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
WITH old AS (
	SELECT
		(SELECT id FROM repositories WHERE repositories.name = repo) AS repository_id,
		trackname,
		count(*) AS refcount
	FROM old_packages
	GROUP BY repo, trackname
), new AS (
	SELECT
		(SELECT id FROM repositories WHERE repositories.name = repo) AS repository_id,
		trackname,
		count(*) AS refcount
	FROM incoming_packages
	GROUP BY repo, trackname
), delta AS (
	SELECT
		repository_id,
		trackname,
		coalesce(new.refcount, 0) - coalesce(old.refcount, 0) AS delta_refcount
	FROM old FULL OUTER JOIN new USING(repository_id, trackname)
	WHERE coalesce(new.refcount, 0) != coalesce(old.refcount, 0)
)
INSERT INTO repo_tracks (
	repository_id,
	trackname,
	refcount
)
SELECT
	repository_id,
	trackname,
	delta_refcount
FROM delta
ON CONFLICT (repository_id, trackname)
DO UPDATE SET
	refcount = repo_tracks.refcount + EXCLUDED.refcount,
	restart_ts = CASE WHEN repo_tracks.refcount = 0 THEN now() ELSE repo_tracks.restart_ts END,
	end_ts = CASE WHEN repo_tracks.refcount + EXCLUDED.refcount = 0 THEN now() ELSE NULL END;

{% if analyze %}
ANALYZE repo_tracks;
{% endif %}
