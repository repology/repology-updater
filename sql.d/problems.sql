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
-- !!get_repository_problems_count(repo) -> single value
--
--------------------------------------------------------------------------------
SELECT
	count(*)
FROM problems
WHERE repo = %(repo)s;


--------------------------------------------------------------------------------
--
-- !!get_repository_problems(repo, limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	repo,
	name,
	effname,
	maintainer,
	problem
FROM problems
WHERE repo = %(repo)s
ORDER BY repo, effname, maintainer
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_maintainer_problems_count(maintainer) -> single value
--
--------------------------------------------------------------------------------
SELECT
	count(*)
FROM problems
WHERE maintainer = %(maintainer)s;


--------------------------------------------------------------------------------
--
-- !!get_maintainer_problems(maintainer, limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	repo,
	name,
	effname,
	maintainer,
	problem
FROM problems
WHERE maintainer = %(maintainer)s
ORDER BY repo, effname, maintainer
LIMIT %(limit)s;
