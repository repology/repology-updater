# Repology

[![Build Status](https://travis-ci.org/repology/repology.svg?branch=master)](https://travis-ci.org/repology/repology)
[![Coverage Status](https://coveralls.io/repos/github/repology/repology/badge.svg?branch=master)](https://coveralls.io/github/repology/repology?branch=master)
[![Code Health](https://landscape.io/github/repology/repology/master/landscape.svg?style=flat)](https://landscape.io/github/repology/repology/master)

Repology tracks and compares package versions in more than 120
package repositories.

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

## Status

Repology is ready to use, official production setup is available
at [repology.org](https://repology.org).

## Repository support

As much data as possible is parsed from each repo. Package name and
version are always parsed.

| Repository                       | Summary | Maint-r | Categ | WWW   | License | Download |
|----------------------------------|:-------:|:-------:|:-----:|:-----:|:-------:|:--------:|
| Alpine                           | ✔       | ✔       |       | ✔     | ✔       |          |
| ALT Sisyphus                     | ✔       | ✔       | ✔     |       |         |          |
| AOSC                             | ✔       |         | ✔     |       |         |          |
| Arch, Parabola, Manjaro          | ✔       | ✔       |       | ✔     | ✔       |          |
| CentOS, Fedora, Mageia, OpenSUSE | ✔       |         | ✔     | ✔     | ✔       |          |
| Chocolatey                       | ✔       |         |       | ✔     |         |          |
| CPAN                             |         | ✔       |       | ✔ (2) |         |          |
| CRAN                             |         |         |       | ✔ (2) |         |          |
| CRUX                             | ✔       | ✔       |       | ✔     |         |          |
| Debian, Ubuntu, other deb-based  |         | ✔       | ✔     | ✔     |         |          |
| DistroWatch.com                  | ✔       |         |       | ✔     |         | ✔        |
| F-Droid                          |         |         | ✔     | ✔     | ✔       |          |
| FreeBSD                          | ✔       | ✔       | ✔     | ✔     |         |          |
| freshcode.club                   | ✔       |         |       | ✔     | ✔       |          |
| Gentoo, Funtoo                   | ✔       | ✔       | ✔     | ✔     | ✔ (1)   | ✔ (1)    |
| Guix                             | ✔       |         |       | ✔     | ✔       |          |
| GoboLinux                        | ✔       |         |       | ✔     | ✔       |          |
| Hackage                          |         |         |       | ✔ (2) |         |          |
| HaikuPorts                       |         |         | ✔     |       |         |          |
| Homebrew                         | ✔       |         |       | ✔     |         |          |
| KaOS                             |         |         |       |       |         |          |
| Linuxbrew                        | ✔       |         |       | ✔     |         |          |
| MacPorts                         | ✔       | ✔       | ✔     | ✔     | ✔       |          |
| MX Linux                         |         | ✔       | ✔     | ✔     |         |          |
| nixpkgs                          | ✔       | ✔       |       | ✔     | ✔       |          |
| OpenBSD                          | ✔       | ✔       | ✔     |       |         |          |
| OpenIndiana                      | ✔       |         | ✔     | ✔     |         | ✔        |
| OpenMandriva                     | ✔       | ✔       | ✔     | ✔     | ✔       |          |
| PCLinuxOS                        | ✔       | ✔       | ✔     |       |         |          |
| pkgsrc                           | ✔       | ✔       | ✔     |       |         |          |
| PyPi                             | ✔       |         |       | ✔ (2) |         |          |
| Ravenports                       | ✔       |         | ✔     | ✔     |         |          |
| RubyGems                         |         |         |       | ✔ (2) |         |          |
| SlackBuilds                      |         | ✔       | ✔     | ✔     |         | ✔        |
| Vcpkg                            | ✔       |         |       |       |         |          |
| YACP                             |         |         |       |       |         |          |

(1) Gentoo support is not complete, complex cases like condional downloads and licenses
are ignored for now.

(2) WWWs are autogenerated for upstream package repos like CPAN, PyPi and Hackage

## Documentation

- How to [run](docs/RUNNING.md) repology tools on your own
- How to extend or fix [rules](docs/RULES.md) for package matching
- How repology [compares versions](https://github.com/repology/libversion/blob/master/doc/ALGORITHM.md)

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
