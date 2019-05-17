# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import datetime
import random
import sys

import flask

from pytz import timezone, utc

from repologyapp.config import config
from repologyapp.globals import get_text_width, repometadata
from repologyapp.template_filters import css_for_versionclass, maintainer_to_links, maintainers_to_group_mailto, pkg_format
from repologyapp.template_functions import endpoint_like, url_for_self
from repologyapp.template_tests import for_page, is_fallback_maintainer
from repologyapp.views import registry as view_registry

# create application and handle configuration
app = flask.Flask(__name__)

# translate some repology config items to flask
if 'SECRET_KEY' not in config:
    print('Error: SECRET_KEY is required to be set in the configuration', file=sys.stderr)
    sys.exit(1)

app.config['SECRET_KEY'] = config['SECRET_KEY']

# templates: tuning
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# templates: custom filters
app.jinja_env.filters['pkg_format'] = pkg_format
app.jinja_env.filters['css_for_versionclass'] = css_for_versionclass
app.jinja_env.filters['maintainer_to_links'] = maintainer_to_links
app.jinja_env.filters['maintainers_to_group_mailto'] = maintainers_to_group_mailto
app.jinja_env.filters['text_width'] = get_text_width

# templates: custom tests
app.jinja_env.tests['for_page'] = for_page
app.jinja_env.tests['fallback_maintainer'] = is_fallback_maintainer

# templates: custom global functions
app.jinja_env.globals['url_for_self'] = url_for_self

# templates: custom global data
app.jinja_env.globals['REPOLOGY_HOME'] = config['REPOLOGY_HOME']
app.jinja_env.globals['repometadata'] = repometadata
app.jinja_env.globals['config'] = config
app.jinja_env.globals['tz'] = timezone(config['DEFAULT_TIMEZONE'])
app.jinja_env.globals['utc'] = utc
app.jinja_env.globals['now'] = lambda: datetime.datetime.now(utc)
app.jinja_env.globals['randrange'] = random.randrange
app.jinja_env.globals['endpoint_like'] = endpoint_like

view_registry.register_in_flask(app)
