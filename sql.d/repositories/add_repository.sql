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
INSERT INTO repositories(
	id,
	name,
	state,

	first_seen,
	last_seen,

	metadata,

	sortname,
	"type",
	"desc",
	statsgroup,
	singular,
	family,
	color,
	shadow,
	incomplete,
	repolinks,
	packagelinks
) VALUES (
	(
		SELECT min(allids.id)
		FROM (
			SELECT
				generate_series(
					1,
					(
						SELECT coalesce(max(id), 1) + 1
						FROM repositories
					)
				) id
		) AS allids
		LEFT OUTER JOIN repositories USING (id)
		WHERE repositories.id IS NULL
	),
	%(metadata)s::json->>'name',
	'new'::repository_state,

	now(),
	now(),

	%(metadata)s,

	%(metadata)s::json->>'sortname',
	%(metadata)s::json->>'type',
	%(metadata)s::json->>'desc',
	%(metadata)s::json->>'statsgroup',
	%(metadata)s::json->>'singular',
	%(metadata)s::json->>'family',
	%(metadata)s::json->>'color',
	(%(metadata)s::json->>'shadow')::boolean,
	(%(metadata)s::json->>'incomplete')::boolean,
	%(metadata)s::json->'repolinks',
	%(metadata)s::json->'packagelinks'
);
