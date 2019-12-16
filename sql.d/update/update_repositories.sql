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
-- Update aggregate tables: repositories, pass1
--------------------------------------------------------------------------------
UPDATE repositories
SET
	num_packages = tmp.num_packages,
	num_packages_newest = tmp.num_packages_newest,
	num_packages_outdated = tmp.num_packages_outdated,
	num_packages_ignored = tmp.num_packages_ignored,
	num_packages_unique = tmp.num_packages_unique,
	num_packages_devel = tmp.num_packages_devel,
	num_packages_legacy = tmp.num_packages_legacy,
	num_packages_incorrect = tmp.num_packages_incorrect,
	num_packages_untrusted = tmp.num_packages_untrusted,
	num_packages_noscheme = tmp.num_packages_noscheme,
	num_packages_rolling = tmp.num_packages_rolling,

	num_metapackages = tmp.num_metapackages,
	num_metapackages_unique = tmp.num_metapackages_unique,
	num_metapackages_newest = tmp.num_metapackages_newest,
	num_metapackages_outdated = tmp.num_metapackages_outdated,
	num_metapackages_comparable = tmp.num_metapackages_comparable,
	num_metapackages_problematic = tmp.num_metapackages_problematic,

	last_seen = now()
FROM (
	SELECT
		repo,

		sum(num_packages) AS num_packages,
		sum(num_packages_newest) AS num_packages_newest,
		sum(num_packages_outdated) AS num_packages_outdated,
		sum(num_packages_ignored) AS num_packages_ignored,
		sum(num_packages_unique) AS num_packages_unique,
		sum(num_packages_devel) AS num_packages_devel,
		sum(num_packages_legacy) AS num_packages_legacy,
		sum(num_packages_incorrect) AS num_packages_incorrect,
		sum(num_packages_untrusted) AS num_packages_untrusted,
		sum(num_packages_noscheme) AS num_packages_noscheme,
		sum(num_packages_rolling) AS num_packages_rolling,

		count(*) AS num_metapackages,
		count(*) FILTER (WHERE "unique") AS num_metapackages_unique,
		count(*) FILTER (WHERE NOT "unique" AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) AS num_metapackages_newest,
		count(*) FILTER (WHERE num_packages_outdated > 0) AS num_metapackages_outdated,
		count(*) FILTER (WHERE
			-- newest
			(NOT "unique" AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) OR
			-- outdated
			(num_packages_outdated > 0) OR
			-- problematic subset
			(num_packages_incorrect > 0)
		) AS num_metapackages_comparable,
		count(*) FILTER (WHERE
			num_packages_ignored > 0 OR
			num_packages_incorrect > 0 OR
			num_packages_untrusted > 0
		) AS num_metapackages_problematic
	FROM (
		SELECT
			repo,
			effname,
			count(*) AS num_packages,
			count(*) FILTER (WHERE versionclass = 1) AS num_packages_newest,
			count(*) FILTER (WHERE versionclass = 2) AS num_packages_outdated,
			count(*) FILTER (WHERE versionclass = 3) AS num_packages_ignored,
			count(*) FILTER (WHERE versionclass = 4) AS num_packages_unique,
			count(*) FILTER (WHERE versionclass = 5) AS num_packages_devel,
			count(*) FILTER (WHERE versionclass = 6) AS num_packages_legacy,
			count(*) FILTER (WHERE versionclass = 7) AS num_packages_incorrect,
			count(*) FILTER (WHERE versionclass = 8) AS num_packages_untrusted,
			count(*) FILTER (WHERE versionclass = 9) AS num_packages_noscheme,
			count(*) FILTER (WHERE versionclass = 10) AS num_packages_rolling,
			max(num_families) = 1 AS "unique"
		FROM packages INNER JOIN metapackages USING(effname)
		WHERE num_repos_nonshadow > 0
		GROUP BY effname, repo
	) AS tmp1
	GROUP BY repo
) AS tmp
WHERE name = tmp.repo;

--------------------------------------------------------------------------------
-- Update aggregate tables: repositories, pass2
--------------------------------------------------------------------------------
UPDATE repositories
SET
	num_maintainers = (
		SELECT
			count(DISTINCT maintainer)
		FROM (
			SELECT
				unnest(maintainers) AS maintainer
			FROM packages
			WHERE repo = repositories.name
		) as TMP
	);

--------------------------------------------------------------------------------
-- Update aggregate tables: repositories, finalize
--------------------------------------------------------------------------------
UPDATE repositories
SET
	num_packages = 0,
	num_packages_newest = 0,
	num_packages_outdated = 0,
	num_packages_ignored = 0,
	num_packages_unique = 0,
	num_packages_devel = 0,
	num_packages_legacy = 0,
	num_packages_incorrect = 0,
	num_packages_untrusted = 0,
	num_packages_noscheme = 0,
	num_packages_rolling = 0,

	num_metapackages = 0,
	num_metapackages_unique = 0,
	num_metapackages_newest = 0,
	num_metapackages_outdated = 0,
	num_metapackages_comparable = 0,
	num_metapackages_problematic = 0,

	num_problems = 0,

	num_maintainers = 0
WHERE
	last_seen != now();
