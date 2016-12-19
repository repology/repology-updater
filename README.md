# Repology

[![Build Status](https://travis-ci.org/AMDmi3/repology.svg?branch=master)](https://travis-ci.org/AMDmi3/repology)
[![Coverage Status](https://coveralls.io/repos/github/AMDmi3/repology/badge.svg?branch=master)](https://coveralls.io/github/AMDmi3/repology?branch=master)

![Example report](docs/screenshot.png)

Repology tracks and compares package versions along multiple
repositories including Arch, Chocolatey, Debian, Fedora, FreeBSD,
Gentoo, Mageia, OpenBSD, OpenSUSE, pkgsrc, Sisyphus, SlackBuilds,
Ubuntu and more.

## Uses

- **Users**:
  - Compare completeness and freshness of package repositories,
    choose most up to date distro
  - Find out what repositories contain newest versions of packages
    you need
- **Package/port maintainers**:
  - Another way to track new releases of software you package
  - Compete with other distros in keeping up to date
  - Find fellow maintainers to resolve packaging problems together
  - Keep package naming and versioning schemes in sync to other
    repos for your and your user's convenience
- **Software authors**:
  - Keep track of how well your project is packaged
  - Keep in touch with your product package maintainers
  - If you're not using [semantic versioning](http://semver.org/)
    yet, see how useful it is

# Status

Repology is currently in an early phase of development, with a goal
of creating usable utility in a quick and dirty way. For now, it is
usable in two modes: as a command line generator of single HTML
report and a static website generator for [repology.org](repology.org).

## Howto

### Dependencies

- [python3](https://www.python.org/), with the following modules
  - [flask](http://flask.pocoo.org/) web microframework
  - [psycopg](http://initd.org/psycopg/) PostgreSQL adapter for Python
  - [pyyaml](http://pyyaml.org/) YAML parser
  - [requests](http://python-requests.org/) (for fetching some repository data)
- [wget](https://www.gnu.org/software/wget/) (for fetching some repository data)
- [git](https://git-scm.com/) (for fetching some repository data)
- [librpm](http://www.rpm.org/) (for parsing some repository data)
- pkg-config

Repology includes some C utilites, to build them run ```make``` in
project directory.

### Usage

#### Fetching repository data

First, repository data need to be fetched, parsed and optionally
stored in the database. ```repology-update.py``` utility does that:

```
./repology-update \
    --statedir=repology.state \
    --fetch --fetch --parse \
    production
```

* ```--statedir``` specifies where to store intermediary data.
* ```--fetch``` tells the utility to fetch raw repository data
(download files, scrape websites, clone git repos), specifying it
allows updating the data (otherwise it's only fetched once).
* ```--parse``` parses downloaded raw data into internal format.
Parsed data is also stored in statedir.
* Free arguments specify list of repositories or tags (tag is a
group of repositories) to work on. Here we only process ```production```
tag.

Statedir defaults to ```_state``` in current directory and list of
repositories defaults to all known repositories, so you may omit these.

After data is downloaded you may inspect it with

```
./repology-dump.py | less
```

The utility allows filtering and several modes of operation, see
```--help``` for full list of options.

#### Filling the database

If the above steps work for you, you may want to run repology web
application. For that you'll need to create PostgreSQL database:

```
CREATE DATABASE repology;
CREATE USER repology WITH PASSWORD 'repology';
GRANT ALL ON DATABASE repology TO repology;
```

Note that you may want to change database, user name and password.

After database is created, make ```repology-update.py``` fill it.

* Add ```--database``` argument to tell the utility to fill database.
Specify twice to (re)initialize the database (you'll need to do this
first time).
* Specify ```--dsn="dbname=DBNAME user=USERNAME password=PASS"```
if you've used custom database setup. Omit to use default
repology/repology/repology.

Summarizing, the minimal command to update all repositories and
store them in the database created as mentioned above is:

```
./repology-update --fetch --fetch --parse --database
```

#### Running the webapp

Repology is a flask application, so you may just run it locally:

```
./repology-app.py
```

and then point your browser to http://127.0.0.1:5000/ to view the
site. This should be enough for personal usage, experiments and
testing.

Alternatively, you may deploy the application in numerous ways,
including mod_wsgi, uwsgi, fastcgi and plain CGI application. See
[flask documentation on deployment](http://flask.pocoo.org/docs/0.11/deploying/)
for more info.

There's a bunch of application settings you may want to tune (most
importantly, DSN). These are taken from ```repology.conf.default```,
but instead of modifying it copy it to ```repology.conf``` and
override values there. You may also set ```REPOLOGY_SETTINGS```
environment variable to the path to your custom config, which
takes the highest priority.

## Repository support

| Repository                       | Name | Ver | Summary | Maint-r | Categ | WWW | License | Download |
|----------------------------------|:----:|:---:|:-------:|:-------:|:-----:|:---:|:-------:|:--------:|
| FreeBSD                          | ✔    | ✔   | ✔       | ✔       | ✔     | ✔   |         |          |
| Debian/Ubuntu                    | ✔    | ✔   |         | ✔       | ✔     | ✔   |         |          |
| Gentoo                           | ✔    | ✔   |         | ✔       | ✔     |     |         |          |
| pkgsrc                           | ✔    | ✔   | ✔       | ✔       | ✔     |     |         |          |
| OpenBSD                          | ✔    | ✔   | ✔       | ✔       | ✔     |     |         |          |
| Arch                             | ✔    | ✔   | ✔       | ✔       |       | ✔   | ✔       |          |
| CentOS, Fedora, Mageia, OpenSUSE | ✔    | ✔   | ✔       |         | ✔     | ✔   | ✔       |          |
| Sisyphus                         | ✔    | ✔   | ✔       | ✔       | ✔     |     |         |          |
| Chocolatey                       | ✔    | ✔   | ✔       |         |       | ✔   |         |          |
| SlackBuilds                      | ✔    | ✔   |         | ✔       | ✔     | ✔   |         | ✔        |
| freshcode.club                   | ✔    | ✔   | ✔       | n/a     |       | ✔   |         |          |
| CPAN                             | ✔    | ✔   |         | ✔       |       | ✔   |         |          |
| PyPi                             | ✔    | ✔   | ✔       |         |       | ✔   |         |          |
| F-Droid                          | ✔    | ✔   |         |         | ✔     | ✔   | ✔       |          |

### FreeBSD

Parses data from INDEX-11.bz2.

TODO: Parsing port Makefiles may extract additional info such as
licenses and options.

Links:
- [FreshPorts](http://freshports.org)
- [SVN](https://svnweb.freebsd.org/ports/head)

### Debian/Ubuntu

Parses data from Sources.gz. Maintainers are taken from both ```Maintainer``` and ```Uploader``` fields.

TODO: May need to parse ```*.debian.tar.xz``` for additional info for
each package. Heavy?

Links:
- [https://www.debian.org/distrib/packages#search_packages](Debian Packages)
- [http://packages.ubuntu.com/](Ubuntu Packages)

### Gentoo

Parses git mirror of portage repository (file tree only, doesn't
look into ebuilds).

TODO: Parse ebuilds for more info.

Links:
- [Gentoo packages](https://packages.gentoo.org/)

### pkgsrc

Parses INDEX file (format similar to FreeBSD).

Lacks maintainer for ~24 ports which use OWNER instead because
OWNER does not get to INDEX.

Links:
- [pkgsrc.org](http://pkgsrc.org/)
- [CVS](http://cvsweb.netbsd.org/bsdweb.cgi/pkgsrc/)
- [pkgsrc.se](http://www.pkgsrc.se/)

### OpenBSD

Parses INDEX file (format similar to FreeBSD).

Links:
- [CVS](http://cvsweb.openbsd.org/cgi-bin/cvsweb/ports/)
- [openports.se](http://openports.se/)

### Arch

Parses package databases (core, extra, community).

Links:
- [Package Search](https://www.archlinux.org/packages/)

### Fedora, Mageia, CentOS, OpenSUSE

Parses source package lists.

Links
- [Fedora Repository](https://mirror.yandex.ru/fedora/linux/development/rawhide/Everything/source/tree/)
- [Fedora Package Database](https://admin.fedoraproject.org/pkgdb)
- [Fedora GIT Repositories](http://pkgs.fedoraproject.org/cgit/rpms/)
- [CentOS Repository](http://vault.centos.org/centos/7/os/Source/)
- [CentOS Packages](http://centos-packages.com/)
- [Mageia Repository](https://mirrors.kernel.org/mageia/distrib/cauldron/SRPMS/core/release/)
- [Mageia App Db](https://madb.mageia.org/)
- [OpenSUSE Repository](http://download.opensuse.org/tumbleweed/repo/src-oss/suse/)
- [OpenSUSE ](https://software.opensuse.org/)

### Sisyphus

Parses srclist.classic files with custom C utility.

Links:
- [Sisyphus repository](http://www.sisyphus.ru/en/)

### Chocolatey

Parses XML descriptions of packages from chocolatey API.

Links:
- [Chocolatey packages](https://chocolatey.org/packages)

### SlackBuilds

Parses .info files from SlackBuilds.

Links:
- [SlackBuilds.org](https://slackbuilds.org/)

### freshcode.club

Parses feed of version updates from freshcode.club.
Since feed only contains 100 latest updates, it is accumulated in
the state file with each update. Entries with highest vesion number
are preserved.

Links:
- [freshcode.club](http://freshcode.club/)

### CPAN

Parses CPAN 02packages.details.txt index.

Links:
- [CPAN](http://search.cpan.org/)

### PyPi

Parses PyPi HTML index.

Links:
- [PyPi](https://pypi.python.org/pypi)

### F-Droid

Parses F-Droid package index XML. Is not enabled yet as most packages
are android-unique, and, even if these are ports of PC software, have
different versioning schemas. Probably it's best to support F-Droid
packages on opt-in basis.

Links:
- [XML index](https://f-droid.org/repo/index.xml)

## Reading the report

Report is HTML table, columns correspond to repositories and rows
correspond to packages. Cells hold package versions, highlighted
as follows:

- ```cyan```: package is only present in a single repo: nothing to
              compare version to, and may be local artifact
- ```green```: package up to date
- ```red```: package outdated (there's newer version in some other repo)
- ```yellow```: there are multiple packages some of which are up to date
                and others are outdated
- ```gray```: version was manually ignored, likely because of broken
              versioning scheme

Note that there may be multiple packages of a same name in a single repo
(either naturally, or because of name transformations).

## Package matching

Some packages are named differently across separate repositories,
so package name transformations are performed to merge differently
named packages into a single entity. [rules.yaml](rules.yaml) contains
rules for such transformation, is in YAML format containing array
of rules. Each rule may contain:

- Matching conditions:
  - ```repo```: only apply rule to repositories of specific type
    (currently ```freebsd```, ```debian```, ```gentoo```, ```pkgsrc```,
     or ```openbsd``` note that these are NOT repository names)
  - ```name```: apply to package of specified name
  - ```namepat```: apply to package with name matching specified regexp
  - ```verpat```: apply to package with version matching specified regexp

- Actions:
  - ```ignore```: completely ignore the package
  - ```setname```: set package name to an argument. ```$0``` is replaced
    with old name, ```$1```, ```$2``` and so on may be used to refer
    capture groups in ```namepat``` regexp, if it's present
  - ```pass```: leave package as is. Useful to prevent following rules
    from matching

Only first matching rule applies. If no rule applies (or ```pass```
rule applies), package data is not modified. Afterwards, regardless
of whether any rule matched, name is always converted to lowercase
and underscores (```_```) replaced with hyphens (```-```).

Note that transformation may merge several packages into single
entry. If they are unrelated this may be a problem (solved by giving
them unique names by rules based on e.g category), otherwise it is
useful and may be done intentionally to merge variants or parts of
specific project into single entity (e.g. merge ```freeciv-client```
and ```freeciv-server``` into ```freeciv``` in pkgsrc, to match
them both against ```freeciv``` in other repos, or match ```fltk15```,
```fltk16```, ```fltk17``` into just ```fltk``` and look at newest
version).

### Example

Debian has ```botan1.10```, FreeBSD has ```botan110``` and other
repos have ```botan```. To merge these into single entity:

```
- { repo: debian, name: botan1.10, setname: botan }
- { repo: freebsd, name: botan110, setname: botan }
```

FreeBSD names Perl module ports as ```p5-My-Module```, Debian does
```libmy-module-perl```, and Gentoo just places ```My-Module``` under
```dev-perl``` category. To merge all these perl modules into single
synthetic ```perl:my-module``` entry (and actually do the same to
all perl modules at once):

```
- { repo: freebsd, namepat: "p5-(.*)",      setname: "perl:$1" }
- { repo: debian,  namepat: "lib(.*)-perl", setname: "perl:$1" }
- { repo: gentoo,  category: dev-perl,      setname: "perl:$0" }
```

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
