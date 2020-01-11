-- Copyright (C) 2018-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param metadata
--------------------------------------------------------------------------------
UPDATE repositories
SET
	state = CASE WHEN state = 'legacy' THEN 'readded'::repository_state ELSE state END,
	last_seen = now(),

	sortname = %(metadata)s::json->>'sortname',
	"type" = %(metadata)s::json->>'type',
	"desc" = %(metadata)s::json->>'desc',
	statsgroup = %(metadata)s::json->>'statsgroup',
	singular = %(metadata)s::json->>'singular',
	family = %(metadata)s::json->>'family',
	color = %(metadata)s::json->>'color',
	shadow = (%(metadata)s::json->>'shadow')::boolean,
	repolinks = %(metadata)s::json->'repolinks',
	packagelinks = %(metadata)s::json->'packagelinks'
WHERE
	name = %(metadata)s::json->>'name';
