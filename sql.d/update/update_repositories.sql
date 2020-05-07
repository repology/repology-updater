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

WITH old_countable_projects AS (
	SELECT
		effname,
		count(DISTINCT family) = 1 AS is_unique
	FROM old_packages
	GROUP BY effname
	HAVING count(*) FILTER (WHERE NOT shadow) > 0  -- exclude shadow-only
), old AS (
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
		sum(num_packages_vulnerable) AS num_packages_vulnerable,

		count(*) AS num_metapackages,
		count(*) FILTER (WHERE is_unique) AS num_metapackages_unique,
		count(*) FILTER (WHERE NOT is_unique AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) AS num_metapackages_newest,
		count(*) FILTER (WHERE num_packages_outdated > 0) AS num_metapackages_outdated,
		count(*) FILTER (WHERE
			-- newest
			(NOT is_unique AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) OR
			-- outdated
			(num_packages_outdated > 0) OR
			-- problematic subset
			(num_packages_incorrect > 0)
		) AS num_metapackages_comparable,
		count(*) FILTER (WHERE
			num_packages_ignored > 0 OR
			num_packages_incorrect > 0 OR
			num_packages_untrusted > 0
		) AS num_metapackages_problematic,
		count(*) FILTER (WHERE
			num_packages_vulnerable > 0
		) AS num_metapackages_vulnerable
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
			count(*) FILTER (WHERE (flags & (1 << 16))::boolean) AS num_packages_vulnerable
		FROM old_packages
		GROUP BY repo, effname
	) AS tmp INNER JOIN old_countable_projects USING(effname)
	GROUP BY repo
), new_countable_projects AS (
	SELECT
		effname,
		count(DISTINCT family) = 1 AS is_unique
	FROM incoming_packages
	GROUP BY effname
	HAVING count(*) FILTER (WHERE NOT shadow) > 0  -- exclude shadow-only
), new AS (
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
		sum(num_packages_vulnerable) AS num_packages_vulnerable,

		count(*) AS num_metapackages,
		count(*) FILTER (WHERE is_unique) AS num_metapackages_unique,
		count(*) FILTER (WHERE NOT is_unique AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) AS num_metapackages_newest,
		count(*) FILTER (WHERE num_packages_outdated > 0) AS num_metapackages_outdated,
		count(*) FILTER (WHERE
			-- newest
			(NOT is_unique AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) OR
			-- outdated
			(num_packages_outdated > 0) OR
			-- problematic subset
			(num_packages_incorrect > 0)
		) AS num_metapackages_comparable,
		count(*) FILTER (WHERE
			num_packages_ignored > 0 OR
			num_packages_incorrect > 0 OR
			num_packages_untrusted > 0
		) AS num_metapackages_problematic,
		count(*) FILTER (WHERE
			num_packages_vulnerable > 0
		) AS num_metapackages_vulnerable
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
			count(*) FILTER (WHERE (flags & (1 << 16))::boolean) AS num_packages_vulnerable
		FROM incoming_packages
		GROUP BY repo, effname
	) AS tmp INNER JOIN new_countable_projects USING(effname)
	GROUP BY repo
), delta AS (
	SELECT
		repo,

		coalesce(new.num_packages, 0) - coalesce(old.num_packages, 0) AS num_packages,
		coalesce(new.num_packages_newest, 0) - coalesce(old.num_packages_newest, 0) AS num_packages_newest,
		coalesce(new.num_packages_outdated, 0) - coalesce(old.num_packages_outdated, 0) AS num_packages_outdated,
		coalesce(new.num_packages_ignored, 0) - coalesce(old.num_packages_ignored, 0) AS num_packages_ignored,
		coalesce(new.num_packages_unique, 0) - coalesce(old.num_packages_unique, 0) AS num_packages_unique,
		coalesce(new.num_packages_devel, 0) - coalesce(old.num_packages_devel, 0) AS num_packages_devel,
		coalesce(new.num_packages_legacy, 0) - coalesce(old.num_packages_legacy, 0) AS num_packages_legacy,
		coalesce(new.num_packages_incorrect, 0) - coalesce(old.num_packages_incorrect, 0) AS num_packages_incorrect,
		coalesce(new.num_packages_untrusted, 0) - coalesce(old.num_packages_untrusted, 0) AS num_packages_untrusted,
		coalesce(new.num_packages_noscheme, 0) - coalesce(old.num_packages_noscheme, 0) AS num_packages_noscheme,
		coalesce(new.num_packages_rolling, 0) - coalesce(old.num_packages_rolling, 0) AS num_packages_rolling,
		coalesce(new.num_packages_vulnerable, 0) - coalesce(old.num_packages_vulnerable, 0) AS num_packages_vulnerable,

		coalesce(new.num_metapackages, 0) - coalesce(old.num_metapackages, 0) AS num_metapackages,
		coalesce(new.num_metapackages_unique, 0) - coalesce(old.num_metapackages_unique, 0) AS num_metapackages_unique,
		coalesce(new.num_metapackages_newest, 0) - coalesce(old.num_metapackages_newest, 0) AS num_metapackages_newest,
		coalesce(new.num_metapackages_outdated, 0) - coalesce(old.num_metapackages_outdated, 0) AS num_metapackages_outdated,
		coalesce(new.num_metapackages_comparable, 0) - coalesce(old.num_metapackages_comparable, 0) AS num_metapackages_comparable,
		coalesce(new.num_metapackages_problematic, 0) - coalesce(old.num_metapackages_problematic, 0) AS num_metapackages_problematic,
		coalesce(new.num_metapackages_vulnerable, 0) - coalesce(old.num_metapackages_vulnerable, 0) AS num_metapackages_vulnerable
	FROM old FULL OUTER JOIN new USING(repo)
)
UPDATE repositories
SET
	num_packages = repositories.num_packages + delta.num_packages,
	num_packages_newest = repositories.num_packages_newest + delta.num_packages_newest,
	num_packages_outdated = repositories.num_packages_outdated + delta.num_packages_outdated,
	num_packages_ignored = repositories.num_packages_ignored + delta.num_packages_ignored,
	num_packages_unique = repositories.num_packages_unique + delta.num_packages_unique,
	num_packages_devel = repositories.num_packages_devel + delta.num_packages_devel,
	num_packages_legacy = repositories.num_packages_legacy + delta.num_packages_legacy,
	num_packages_incorrect = repositories.num_packages_incorrect + delta.num_packages_incorrect,
	num_packages_untrusted = repositories.num_packages_untrusted + delta.num_packages_untrusted,
	num_packages_noscheme = repositories.num_packages_noscheme + delta.num_packages_noscheme,
	num_packages_rolling = repositories.num_packages_rolling + delta.num_packages_rolling,
	num_packages_vulnerable = repositories.num_packages_vulnerable + delta.num_packages_vulnerable,

	num_metapackages = repositories.num_metapackages + delta.num_metapackages,
	num_metapackages_unique = repositories.num_metapackages_unique + delta.num_metapackages_unique,
	num_metapackages_newest = repositories.num_metapackages_newest + delta.num_metapackages_newest,
	num_metapackages_outdated = repositories.num_metapackages_outdated + delta.num_metapackages_outdated,
	num_metapackages_comparable = repositories.num_metapackages_comparable + delta.num_metapackages_comparable,
	num_metapackages_problematic = repositories.num_metapackages_problematic + delta.num_metapackages_problematic,
	num_metapackages_vulnerable = repositories.num_metapackages_vulnerable + delta.num_metapackages_vulnerable
FROM delta
WHERE
	repositories.name = delta.repo;
