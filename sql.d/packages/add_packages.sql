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

--------------------------------------------------------------------------------
--
-- @param many objects
--
--------------------------------------------------------------------------------
INSERT INTO incoming_packages (
	-- parsed, immutable
	repo,
	family,
	subrepo,

	name,
	srcname,
	binname,
	visiblename,
	projectname_seed,
	trackname,

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

	-- calculated
	effname,

	version,
	versionclass,

	flags,
	shadow,

	flavors,
	branch
) VALUES (
	-- parsed, immutable
	%(repo)s,
	%(family)s,
	%(subrepo)s,

	%(name)s,
	%(srcname)s,
	%(binname)s,
	%(visiblename)s,
	%(projectname_seed)s,
	%(trackname)s,

	%(origversion)s,
	%(rawversion)s,

	%(arch)s,

	%(maintainers)s,
	%(category)s,
	%(comment)s,
	%(homepage)s,
	%(licenses)s,
	%(downloads)s,

	%(extrafields)s,

	%(cpe_vendor)s,
	%(cpe_product)s,

	-- calculated
	%(effname)s,

	%(version)s,
	%(versionclass)s,

	%(flags)s,
	%(shadow)s,

	%(flavors)s,
	%(branch)s
)
