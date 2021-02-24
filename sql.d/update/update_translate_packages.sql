-- Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

INSERT INTO incoming_packages (
	repo,
	family,
	subrepo,

	name,
	srcname,
	binname,
	binnames,
	trackname,
	visiblename,
	projectname_seed,

	origversion,
	rawversion,

	arch,

	maintainers,
	category,
	comment,
	homepage,
	licenses,
	downloads,

	extrafields,

	cpe_vendor,
	cpe_product,
	cpe_edition,
	cpe_lang,
	cpe_sw_edition,
	cpe_target_sw,
	cpe_target_hw,
	cpe_other,

	links,

	effname,

	version,
	versionclass,

	flags,
	shadow
)
SELECT
	repo,
	family,
	subrepo,

	name,
	srcname,
	binname,
	binnames,
	trackname,
	visiblename,
	projectname_seed,

	origversion,
	rawversion,

	arch,

	maintainers,
	category,
	comment,
	homepage,
	licenses,
	downloads,

	extrafields,

	cpe_vendor,
	cpe_product,
	cpe_edition,
	cpe_lang,
	cpe_sw_edition,
	cpe_target_sw,
	cpe_target_hw,
	cpe_other,

	translate_links(links),

	effname,

	version,
	versionclass,

	flags,
	shadow
FROM incoming_packages_raw;
