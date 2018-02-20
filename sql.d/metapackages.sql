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

-- !!get_metapackage_packages(effname) -> array of packages
SELECT
	repo,
	family,
	subrepo,

	name,
	effname,

	version,
	origversion,
	versionclass,

	maintainers,
	category,
	comment,
	homepage,
	licenses,
	downloads,

	flags,
	shadow,
	verfixed,

	flavors,

	extrafields
FROM packages
WHERE effname = %(effname)s;

-- !!get_metapackages_packages(effnames) -> array of packages
SELECT
	repo,
	family,
	subrepo,

	name,
	effname,

	version,
	origversion,
	versionclass,

	maintainers,
	category,
	comment,
	homepage,
	licenses,
	downloads,

	flags,
	shadow,
	verfixed,

	flavors,

	extrafields
FROM packages
WHERE effname = ANY(%(effnames)s);

-- !!get_metapackage_related_metapackages(effname, limit) -> array of packages
SELECT
	repo,
	family,
	subrepo,

	name,
	effname,

	version,
	origversion,
	versionclass,

	maintainers,
	category,
	comment,
	homepage,
	licenses,
	downloads,

	flags,
	shadow,
	verfixed,

	flavors,

	extrafields
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

-- !!get_all_metapackage_names_by_min_spread_count(spread) -> single value
SELECT
	count(DISTINCT effname)
FROM metapackage_repocounts
WHERE num_families >= %(spread)s;

-- !!get_all_metapackage_names_by_min_spread(spread, limit=None) -> array of values
SELECT DISTINCT
	effname
FROM metapackage_repocounts
WHERE num_families >= %(spread)s
LIMIT %(limit)s;

-- !!get_all_metapackage_names_by_spread(spread, limit=None) -> array of values
SELECT DISTINCT
	effname
FROM metapackage_repocounts
WHERE num_families = %(spread)s
LIMIT %(limit)s;
