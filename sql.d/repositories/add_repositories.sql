-- Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param many dicts
--
--------------------------------------------------------------------------------
INSERT INTO repositories(
    name,
	state,

    first_seen,
    last_seen,

    sortname,
    "type",
    "desc",
    statsgroup,
    singular,
    family,
    color,
    shadow,
    repolinks,
    packagelinks
) VALUES (
	%(name)s,
	'new'::repository_state,

	now(),
	now(),

	%(sortname)s,
	%(type)s,
	%(desc)s,
	%(statsgroup)s,
	%(singular)s,
	%(family)s,
	%(color)s,
	%(shadow)s,
	%(repolinks)s,
	%(packagelinks)s
)
ON CONFLICT (name)
DO UPDATE SET
	state = 'active'::repository_state,
	sortname = EXCLUDED.sortname,
	"type" = EXCLUDED."type",
	"desc" = EXCLUDED."desc",
	statsgroup = EXCLUDED.statsgroup,
	singular = EXCLUDED.singular,
	family = EXCLUDED.family,
	color = EXCLUDED.color,
	shadow = EXCLUDED.shadow,
	repolinks = EXCLUDED.repolinks,
	packagelinks = EXCLUDED.packagelinks;
