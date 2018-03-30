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
-- !!get_metapackage_packages(effname, fields=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
{% if fields %}
	{{ fields | join(',') }}
{% else %}
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
{% endif %}
FROM packages
WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackages_packages(effnames, fields=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
{% if fields %}
	{{ fields | join(',') }}
{% else %}
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
{% endif %}
FROM packages
WHERE effname = ANY(%(effnames)s);


--------------------------------------------------------------------------------
--
-- !!add_packages(many packages)
--
--------------------------------------------------------------------------------
INSERT INTO packages(
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
) VALUES (
	%(repo)s,
	%(family)s,
	%(subrepo)s,

	%(name)s,
	%(effname)s,

	%(version)s,
	%(origversion)s,
	%(versionclass)s,

	%(maintainers)s,
	%(category)s,
	%(comment)s,
	%(homepage)s,
	%(licenses)s,
	%(downloads)s,

	%(flags)s,
	%(shadow)s,
	%(verfixed)s,

	%(flavors)s,

	%(extrafields)s
)
