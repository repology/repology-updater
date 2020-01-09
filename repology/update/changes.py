# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

from dataclasses import dataclass
from typing import Iterable, List

from repology.package import Package
from repology.update.hashes import ProjectHash, calculate_project_classless_hash


__all__ = [
    'ProjectsChangeStatistics',
    'ChangedProject',
    'RemovedProject',
    'UpdatedProject',
    'iter_changed_projects',
]


@dataclass
class ChangedProject:
    effname: str


@dataclass
class RemovedProject(ChangedProject):
    pass


@dataclass
class UpdatedProject(ChangedProject):
    hash: int
    packages: List[Package]


@dataclass
class ProjectsChangeStatistics:
    added: int = 0
    removed: int = 0
    changed: int = 0
    unchanged: int = 0

    @property
    def total(self) -> int:
        return self.added + self.removed + self.changed + self.unchanged

    @property
    def change_fraction(self) -> float:
        if self.total == 0:
            return 0.0
        return 1.0 - (self.unchanged / self.total)

    def __str__(self) -> str:
        return f'added {self.added}, removed {self.removed}, changed {self.changed}, unchanged {self.unchanged}, total change {self.change_fraction*100.0:.2f}%'


def iter_changed_projects(old_hashes_iter: Iterable[ProjectHash], new_packagesets_iter: Iterable[List[Package]], statistics: ProjectsChangeStatistics) -> Iterable[ChangedProject]:
    old_effname, old_hash = next(old_hashes_iter, (None, None))  # type: ignore
    new_packages = next(new_packagesets_iter, None)  # type: ignore

    while new_packages is not None or old_effname is not None:
        if old_effname is None or (new_packages is not None and new_packages[0].effname < old_effname):
            # only in new (added)
            statistics.added += 1
            yield UpdatedProject(new_packages[0].effname, calculate_project_classless_hash(new_packages), new_packages)
            new_packages = next(new_packagesets_iter, None)  # type: ignore

        elif new_packages is None or old_effname < new_packages[0].effname:
            # only in old (removed)
            statistics.removed += 1
            yield RemovedProject(old_effname)
            old_effname, old_hash = next(old_hashes_iter, (None, None))  # type: ignore

        else:
            # in both
            new_hash = calculate_project_classless_hash(new_packages)

            if new_hash != old_hash:
                statistics.changed += 1
                yield UpdatedProject(old_effname, new_hash, new_packages)
            else:
                statistics.unchanged += 1

            new_packages = next(new_packagesets_iter, None)  # type: ignore
            old_effname, old_hash = next(old_hashes_iter, (None, None))  # type: ignore
