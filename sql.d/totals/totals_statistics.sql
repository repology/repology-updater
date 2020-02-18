-- Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param do_fix=False
-- @returns array of dicts
--------------------------------------------------------------------------------
WITH actual AS (
	SELECT num_packages FROM statistics
), expected AS (
	SELECT count(*) AS num_packages FROM packages
)
{% if do_fix %}
, fix AS (
	UPDATE statistics
	SET
		num_packages = (SELECT num_packages FROM expected)
)
{% endif %}
SELECT
	row_to_json(actual) AS actual,
	row_to_json(expected) AS expected
FROM
	expected FULL OUTER JOIN actual ON true
WHERE
	actual.num_packages != expected.num_packages
;
