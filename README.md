# Repology

[![Build Status](https://travis-ci.org/repology/repology-updater.svg?branch=master)](https://travis-ci.org/repology/repology-updater)
[![codecov](https://codecov.io/gh/repology/repology-updater/branch/master/graph/badge.svg)](https://codecov.io/gh/repology/repology-updater)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ac95ded5d51f4181bf65dc90b0eb5e12)](https://www.codacy.com/manual/AMDmi3/repology-updater)

Repology is a service which monitors *a lot* of package repositories
and other sources and aggregates data on software package versions,
reporting new releases and packaging problems.

This repository contains Repology updater code, a backend service
which updates the repository information. See also the
[web application](https://github.com/repology/repology-webapp) code.

## Dependencies

  - [Python](https://www.python.org/) 3.8+
  - Python module [Jinja2](http://jinja.pocoo.org/)
  - Python module [libversion](https://pypi.python.org/pypi/libversion) (also requires [libversion](https://github.com/repology/libversion) C library)
  - Python module [psycopg2](http://initd.org/psycopg/)
  - Python module [pyyaml](http://pyyaml.org/)
  - Python module [xxhash](https://github.com/ifduyue/python-xxhash)
  - [PostgreSQL](https://www.postgresql.org/) 12.0+
  - PostgreSQL extension [libversion](https://github.com/repology/postgresql-libversion)

Needed for fetching/parsing repository data:

  - Python module [requests](http://python-requests.org/)
  - Python module [rubymarshal](https://github.com/d9pouces/RubyMarshal)
  - Python module [lxml](http://lxml.de/)
  - Python module [rpm](http://rpm.org/) (comes with RPM package manager)
  - Python module [jsonslicer](https://pypi.org/project/jsonslicer/)
  - Python module [pyparsing](https://github.com/pyparsing/pyparsing)
  - Python module [protobuf](https://github.com/protocolbuffers/protobuf)
  - Python module sqlite3 (part of Python, sometimes packaged separately)
  - [git](https://git-scm.com/)
  - [rsync](https://rsync.samba.org/)
  - [subversion](https://subversion.apache.org/)

### Development dependencies

Optional, for doing HTML validation when running tests:
  - Python module [pytidylib](https://pypi.python.org/pypi/pytidylib) and [tidy-html5](http://www.html-tidy.org/) library

Optional, for checking schemas of configuration files:
  - Python module [voluptuous](https://pypi.python.org/pypi/voluptuous)

Optional, for python code linting:
  - Python module [flake8](https://pypi.python.org/pypi/flake8)
  - Python module [flake8-builtins](https://pypi.python.org/pypi/flake8-builtins)
  - Python module [flake8-import-order](https://pypi.python.org/pypi/flake8-import-order)
  - Python module [flake8-quotes](https://pypi.python.org/pypi/flake8-quotes)
  - Python module [mypy](http://mypy-lang.org/)

## Running

### Preparing

Since repology rules live in separate repository you'll need to
clone it first. The location may be arbitrary, but `rules.d`
subdirectory is what default configuration file points to, so
using it is the most simple way.

```shell
git clone https://github.com/repology/repology-rules.git rules.d
```

### Configuration

First, you may need to tune settings which are shared by all repology
utilities, such as directory for storing downloaded repository state
or DSN (string which specifies how to connect to PostgreSQL database).
See `repology.conf.default` for default values, create `repology.conf`
in the same directory to override them (don't edit `repology.conf.default`!)
or specify path to alternative config via `REPOLOGY_SETTINGS`
environment variable, or override settings via command line.

By default, repology uses `./_state` directory for storing raw and parsed
repository data and `repology/repology/repology` database/user/password
on localhost.

### Creating the database

For the following steps you'll need to set up the database. Ensure
PostgreSQL server is up and running, and execute the following
commands to create the database for repology:

```shell
psql --username postgres -c "CREATE DATABASE repology"
psql --username postgres -c "CREATE USER repology WITH PASSWORD 'repology'"
psql --username postgres -c "GRANT ALL ON DATABASE repology TO repology"
psql --username postgres --dbname repology -c "CREATE EXTENSION pg_trgm"
psql --username postgres --dbname repology -c "CREATE EXTENSION libversion"
```

in the case you want to change the credentials, don't forget to add
actual ones to `repology.conf`.

Next you can create database schema (tables, indexes etc.) and at the
same time test that the database is accessible with the following command:

```shell
./repology-update.py --initdb
```

### Fetching/updating repository data

The database is now ready to be filled with data. Typical Repology
update cycle consists of multiple steps, but in most cases you'll need
to just run all of them:

```shell
./repology-update.py --fetch --fetch --parse --database --postupdate
```

  - `--fetch` tells the utility to fetch raw repository data
    (download files, scrape websites, clone git repos) into state
    directory. Note that it won't refetch (update) data unless
    it's specified twice.
  - `--parse` enables parsing downloaded data into internal format
    which is also saved into state directory.
  - `--database` pushes processed package data into the database.
  - `--postupdate` runs additional database processing such as
    calculating summaries and updating feeds. It's separate from
    `--database` because it can be ran in background, parallelly
    to the following fetch/update cycle.

## Documentation

  - How to extend or fix [rules](https://github.com/repology/repology-rules/blob/master/README.md) for package matching
  - How repology [compares versions](https://github.com/repology/libversion/blob/master/doc/ALGORITHM.md)

## Author

  - [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
