-- Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

DROP TYPE IF EXISTS metapackage_event_type CASCADE;

CREATE TYPE metapackage_event_type AS enum(
	'history_start',
	'repos_update',
	'version_update',
	'catch_up',
	'history_end'
);

DROP TYPE IF EXISTS maintainer_repo_metapackages_event_type CASCADE;

CREATE TYPE maintainer_repo_metapackages_event_type AS enum(
	'added',
	'uptodate',
	'outdated',
	'ignored',
	'removed'
);

DROP TYPE IF EXISTS global_version_event_type CASCADE;

CREATE TYPE global_version_event_type AS enum(
	'newest_update',
	'devel_update'
);

DROP TYPE IF EXISTS repository_state CASCADE;

CREATE TYPE repository_state AS enum(
	'new',
	'active',
	'legacy',
	'readded'
);

DROP TYPE IF EXISTS run_type CASCADE;

CREATE TYPE run_type AS enum(
	'fetch',
	'parse',
	'database_push',
	'database_postprocess'
);

DROP TYPE IF EXISTS run_status CASCADE;

CREATE TYPE run_status AS enum(
	'running',
	'successful',
	'failed',
	'interrupted'
);

DROP TYPE IF EXISTS log_severity CASCADE;

CREATE TYPE log_severity AS enum(
	'notice',
	'warning',
	'error'
);

DROP TYPE IF EXISTS project_name_type CASCADE;

CREATE TYPE project_name_type AS enum(
	'name',
	'srcname',
	'binname'
);

DROP TYPE IF EXISTS problem_type CASCADE;

CREATE TYPE problem_type AS enum(
	'homepage_dead',
	'homepage_permanent_https_redirect',
	'homepage_discontinued_google',
	'homepage_discontinued_codeplex',
	'homepage_discontinued_gna',
	'homepage_discontinued_cpan',
	'cpe_unreferenced',
	'cpe_missing',
	'download_dead',
	'download_permanent_https_redirect',
	'homepage_sourceforge_missing_trailing_slash'
);
