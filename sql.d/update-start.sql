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

-- !!update_start()
DELETE
FROM packages;

UPDATE repositories
SET
	num_packages = 0,
	num_packages_newest = 0,
	num_packages_outdated = 0,
	num_packages_ignored = 0,
	num_packages_unique = 0,
	num_packages_devel = 0,
	num_packages_legacy = 0,
	num_packages_incorrect = 0,
	num_packages_untrusted = 0,
	num_packages_noscheme = 0,
	num_packages_rolling = 0,
	num_metapackages = 0,
	num_metapackages_unique = 0,
	num_metapackages_newest = 0,
	num_metapackages_outdated = 0,
	num_metapackages_comparable = 0,
	num_problems = 0,
	num_maintainers = 0;

DELETE
FROM problems;

UPDATE statistics
SET
	num_packages = 0,
	num_metapackages = 0,
	num_problems = 0,
	num_maintainers = 0;
