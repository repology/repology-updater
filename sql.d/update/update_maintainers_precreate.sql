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
-- @param analyze=True
--------------------------------------------------------------------------------

WITH old AS (
	SELECT
		unnest(maintainers) AS maintainer_name
	FROM old_packages
), new AS (
	SELECT
		unnest(maintainers) AS maintainer_name
	FROM incoming_packages
)
INSERT INTO maintainers(maintainer)
SELECT
	maintainer_name
FROM old RIGHT OUTER JOIN new USING(maintainer_name)
WHERE old.maintainer_name IS NULL
ON CONFLICT(maintainer)
DO NOTHING;

{% if analyze %}
ANALYZE maintainers;
{% endif %}
