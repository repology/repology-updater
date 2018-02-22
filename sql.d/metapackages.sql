-- Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
--
-- !!query_metapackages_rfevm(pivot=None, reverse=False, search=None, maintainer=None, inrepo=None, notinrepo=None, minspread=None, maxspread=None, category=None, newest=False, outdated=False, newest_single_repo=False, newest_single_family=False, problematic=False, limit=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	repo,
	family,

	effname,

	version,
	versionclass,

	maintainers
FROM packages
WHERE effname IN (
	SELECT effname
	FROM metapackage_repocounts
	WHERE
		(
			true --NOT shadow_only
		) AND (
			-- pivot condition
			%(pivot)s IS NULL OR
			(NOT %(reverse)s AND effname >= %(pivot)s) OR
			(%(reverse)s AND effname <= %(pivot)s)
		) AND (
			-- search condition
			%(search)s IS NULL OR
			effname LIKE ('%%' || %(search)s || '%%')
		) AND (
			-- spread conditions
			%(minspread)s IS NULL OR
			num_families >= %(minspread)s
		) AND (
			%(maxspread)s IS NULL OR
			num_families <= %(maxspread)s
		) AND (
			-- single newest conditions
			NOT %(newest_single_repo)s OR
			num_repos_newest = 1
		) AND (
			NOT %(newest_single_family)s OR
			num_families_newest = 1
		) AND (
			-- in repo condition
			%(inrepo)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						repo = %(inrepo)s
					) AND (
						NOT %(newest)s OR
						num_packages_newest > 0 OR
						num_packages_devel > 0
					) AND (
						NOT %(outdated)s OR
						num_packages_outdated > 0
					) AND (
						NOT %(problematic)s OR
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
		) AND (
			-- not in repo condition
			%(notinrepo)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				GROUP BY effname
				HAVING count(*) FILTER (WHERE repo = %(notinrepo)s) = 0
			)
		) AND (
			-- maintainer condition
			%(maintainer)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM maintainer_metapackages
				WHERE
					(
						maintainer = %(maintainer)s
					) AND (
						NOT %(newest)s OR
						num_packages_newest > 0 OR
						num_packages_devel > 0
					) AND (
						NOT %(outdated)s OR
						num_packages_outdated > 0
					) AND (
						NOT %(problematic)s OR
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
		) AND (
			-- category condition
			%(category)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM category_metapackages
				WHERE category = %(category)s
			)
		) AND (
			-- newest not handled for either maintainer or repo
			NOT %(newest)s OR
			%(inrepo)s IS NOT NULL OR
			%(maintainer)s IS NOT NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_newest > 0 OR
						num_packages_devel > 0
					)
			)
		) AND (
			-- outdated not handled for either maintainer or repo
			NOT %(outdated)s OR
			%(inrepo)s IS NOT NULL OR
			%(maintainer)s IS NOT NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_outdated > 0
					)
			)
		) AND (
			-- problematic not handled for either maintainer or repo
			NOT %(problematic)s OR
			%(inrepo)s IS NOT NULL OR
			%(maintainer)s IS NOT NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
		)
	ORDER BY
		CASE WHEN NOT %(reverse)s THEN effname ELSE NULL END,
		CASE WHEN %(reverse)s THEN effname ELSE NULL END DESC
	LIMIT %(limit)s
);

--------------------------------------------------------------------------------
--
-- !!query_metapackages(pivot=None, reverse=False, search=None, maintainer=None, inrepo=None, notinrepo=None, minspread=None, maxspread=None, category=None, newest=False, outdated=False, newest_single_repo=False, newest_single_family=False, problematic=False, limit=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	*  -- XXX: remove code duplication with query_metapackages_rfevm
FROM packages
WHERE effname IN (
	SELECT effname
	FROM metapackage_repocounts
	WHERE
		(
			true --NOT shadow_only
		) AND (
			-- pivot condition
			%(pivot)s IS NULL OR
			(NOT %(reverse)s AND effname >= %(pivot)s) OR
			(%(reverse)s AND effname <= %(pivot)s)
		) AND (
			-- search condition
			%(search)s IS NULL OR
			effname LIKE ('%%' || %(search)s || '%%')
		) AND (
			-- spread conditions
			%(minspread)s IS NULL OR
			num_families >= %(minspread)s
		) AND (
			%(maxspread)s IS NULL OR
			num_families <= %(maxspread)s
		) AND (
			-- single newest conditions
			NOT %(newest_single_repo)s OR
			num_repos_newest = 1
		) AND (
			NOT %(newest_single_family)s OR
			num_families_newest = 1
		) AND (
			-- in repo condition
			%(inrepo)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						repo = %(inrepo)s
					) AND (
						NOT %(newest)s OR
						num_packages_newest > 0 OR
						num_packages_devel > 0
					) AND (
						NOT %(outdated)s OR
						num_packages_outdated > 0
					) AND (
						NOT %(problematic)s OR
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
		) AND (
			-- not in repo condition
			%(notinrepo)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				GROUP BY effname
				HAVING count(*) FILTER (WHERE repo = %(notinrepo)s) = 0
			)
		) AND (
			-- maintainer condition
			%(maintainer)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM maintainer_metapackages
				WHERE
					(
						maintainer = %(maintainer)s
					) AND (
						NOT %(newest)s OR
						num_packages_newest > 0 OR
						num_packages_devel > 0
					) AND (
						NOT %(outdated)s OR
						num_packages_outdated > 0
					) AND (
						NOT %(problematic)s OR
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
		) AND (
			-- category condition
			%(category)s IS NULL OR
			effname IN (
				SELECT
					effname
				FROM category_metapackages
				WHERE category = %(category)s
			)
		) AND (
			-- newest not handled for either maintainer or repo
			NOT %(newest)s OR
			%(inrepo)s IS NOT NULL OR
			%(maintainer)s IS NOT NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_newest > 0 OR
						num_packages_devel > 0
					)
			)
		) AND (
			-- outdated not handled for either maintainer or repo
			NOT %(outdated)s OR
			%(inrepo)s IS NOT NULL OR
			%(maintainer)s IS NOT NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_outdated > 0
					)
			)
		) AND (
			-- problematic not handled for either maintainer or repo
			NOT %(problematic)s OR
			%(inrepo)s IS NOT NULL OR
			%(maintainer)s IS NOT NULL OR
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
		)
	ORDER BY
		CASE WHEN NOT %(reverse)s THEN effname ELSE NULL END,
		CASE WHEN %(reverse)s THEN effname ELSE NULL END DESC
	LIMIT %(limit)s
);


--------------------------------------------------------------------------------
--
-- !!get_metapackage_packages(effname) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	*
FROM packages
WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackage_packages_rv(effname) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	repo,

	version,
	versionclass
FROM packages
WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackage_families_count(effname) -> single value
--
--------------------------------------------------------------------------------
SELECT count(DISTINCT family) FROM packages WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackages_packages(effnames) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	*
FROM packages
WHERE effname = ANY(%(effnames)s);


--------------------------------------------------------------------------------
--
-- !!get_metapackages_packages_fev(effnames) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	family,

	effname,

	version,
	versionclass
FROM packages
WHERE effname = ANY(%(effnames)s);


--------------------------------------------------------------------------------
--
-- !!get_metapackage_related_metapackages_fev(effname, limit) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
	family,

	effname,

	version,
	versionclass
FROM packages
WHERE effname IN (
	WITH RECURSIVE r AS (
		SELECT
			effname,
			url
		FROM url_relations
		WHERE effname = %(effname)s
		UNION
		SELECT
			url_relations.effname,
			url_relations.url
		FROM url_relations
		JOIN r ON
			url_relations.effname = r.effname OR url_relations.url = r.url
	)
	SELECT DISTINCT
		effname
	FROM r
	ORDER BY effname
	LIMIT %(limit)s
);


--------------------------------------------------------------------------------
--
-- !!get_all_metapackage_names_by_min_spread_count(spread) -> single value
--
--------------------------------------------------------------------------------
SELECT
	count(DISTINCT effname)
FROM metapackage_repocounts
WHERE num_families >= %(spread)s;


--------------------------------------------------------------------------------
--
-- !!get_all_metapackage_names_by_min_spread(spread, limit=None) -> array of values
--
--------------------------------------------------------------------------------
SELECT DISTINCT
	effname
FROM metapackage_repocounts
WHERE num_families >= %(spread)s
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_all_metapackage_names_by_spread(spread, limit=None) -> array of values
--
--------------------------------------------------------------------------------
SELECT DISTINCT
	effname
FROM metapackage_repocounts
WHERE num_families = %(spread)s
LIMIT %(limit)s;
