# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any

import flask


__all__ = ['url_for_self']


def url_for_self(**args: Any) -> Any:
    return flask.url_for(flask.request.endpoint, **dict(flask.request.view_args, **args))


def endpoint_like(*variants: str) -> bool:
    endpoint = flask.request.endpoint

    for variant in variants:
        if endpoint == variant:
            return True
        elif variant.endswith('*') and endpoint and endpoint.startswith(variant[:-1]):
            return True

    return False
