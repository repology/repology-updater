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
-- @param pivot=None
-- @param reverse=False
-- @param search=None
-- @param maintainer=None
-- @param inrepo=None
-- @param notinrepo=None
-- @param min_repos=None
-- @param max_repos=None
-- @param min_families=None
-- @param max_families=None
-- @param min_repos_newest=None
-- @param max_repos_newest=None
-- @param min_families_newest=None
-- @param max_families_newest=None
-- @param category=None
-- @param newest=False
-- @param outdated=False
-- @param problematic=False
-- @param has_related=False
-- @param limit=None
--
-- @returns dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	has_related
FROM metapackages
WHERE
	(
		num_repos_nonshadow > 0
	{% if pivot %}
	) AND (
		-- pivot condition
		{% if reverse %}
		effname <= %(pivot)s
		{% else %}
		effname >= %(pivot)s
		{% endif %}
	{% endif %}
	{% if search %}
	) AND (
		-- search condition
		effname LIKE ('%%' || %(search)s || '%%')
	{% endif %}

	{% if min_repos is not none %}
	) AND (
		num_repos >= %(min_repos)s
	{% endif %}
	{% if max_repos is not none %}
	) AND (
		num_repos <= %(max_repos)s
	{% endif %}
	{% if min_families is not none %}
	) AND (
		num_families >= %(min_families)s
	{% endif %}
	{% if max_families is not none %}
	) AND (
		num_families <= %(max_families)s
	{% endif %}
	{% if min_repos_newest is not none %}
	) AND (
		num_repos_newest >= %(min_repos_newest)s
	{% endif %}
	{% if max_repos_newest is not none %}
	) AND (
		num_repos_newest <= %(max_repos_newest)s
	{% endif %}
	{% if min_families_newest is not none %}
	) AND (
		num_families_newest >= %(min_families_newest)s
	{% endif %}
	{% if max_families_newest is not none %}
	) AND (
		num_families_newest <= %(max_families_newest)s
	{% endif %}

	{% if has_related %}
	) AND (
		has_related
	{% endif %}

	{% if inrepo %}
	) AND (
		-- in repo condition
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			WHERE
				(
					repo = %(inrepo)s
				{% if newest %}
				) AND (
					num_packages_newest > 0 OR num_packages_devel > 0 OR num_packages_unique > 0
				{% endif %}
				{% if outdated %}
				) AND (
					num_packages_outdated > 0
				{% endif %}
				{% if problematic %}
				) AND (
					num_packages_ignored > 0 OR num_packages_incorrect > 0 OR num_packages_untrusted > 0
				{% endif %}
				)
		)
	{% endif %}

	{% if notinrepo %}
	) AND (
		-- not in repo condition
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			GROUP BY effname
			HAVING count(*) FILTER (WHERE repo = %(notinrepo)s) = 0
		)
	{% endif %}

	{% if maintainer %}
	) AND (
		-- maintainer condition
		effname IN (
			SELECT
				effname
			FROM maintainer_metapackages
			WHERE
				(
					maintainer = %(maintainer)s
				{% if newest %}
				) AND (
					newest
				{% endif %}
				{% if outdated %}
				) AND (
					outdated
				{% endif %}
				{% if problematic %}
				) AND (
					problematic
				{% endif %}
				)
		)
	{% endif %}

	{% if category %}
	) AND (
		-- category condition
		effname IN (
			SELECT
				effname
			FROM category_metapackages
			WHERE category = %(category)s
		)
	{% endif %}

	{% if not maintainer and not repo and newest %}
	) AND (
		-- newest not handled for either maintainer or repo
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			WHERE num_packages_newest > 0 OR num_packages_devel > 0 OR num_packages_unique > 0
		)
	{% endif %}
	{% if not maintainer and not repo and outdated %}
	) AND (
		-- outdated not handled for either maintainer or repo
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			WHERE num_packages_outdated > 0
		)
	{% endif %}
	{% if not maintainer and not repo and problematic %}
	) AND (
		-- problematic not handled for either maintainer or repo
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			WHERE num_packages_ignored > 0 OR num_packages_incorrect > 0 OR num_packages_untrusted > 0
		)
	{% endif %}
	)
ORDER BY
	effname{% if reverse %} DESC{% endif %}
LIMIT %(limit)s;
