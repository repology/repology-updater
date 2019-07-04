# Repology

[![Build Status](https://travis-ci.org/repology/repology.svg?branch=master)](https://travis-ci.org/repology/repology)
[![Coverage Status](https://coveralls.io/repos/github/repology/repology/badge.svg?branch=master)](https://coveralls.io/github/repology/repology?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/80aef8f1486a4d7fbf3ab6a60a41af27)](https://www.codacy.com/app/AMDmi3/repology)

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
| Adélie                           | ✔       | ✔       |       | ✔     | ✔       |          |
| AIX Open Source Packages         |         |         |       |       |         |          |
| Alpine                           | ✔       | ✔       |       | ✔     | ✔       |          |
| ALT Sisyphus                     | ✔       | ✔       | ✔     |       |         |          |
| AOSC                             | ✔       |         | ✔     |       |         |          |
| Arch, Parabola, Manjaro          | ✔       | ✔       |       | ✔     | ✔       |          |
| Buckaroo                         |         |         |       | ✔     | ✔       |          |
| CentOS, Fedora, Mageia, OpenSUSE | ✔       |         | ✔     | ✔     | ✔       |          |
| Chocolatey                       | ✔       |         |       | ✔     |         |          |
| CPAN                             |         | ✔       |       | ✔ (2) |         |          |
| CRAN                             |         |         |       | ✔ (2) |         |          |
| crates.io                        | ✔       |         |       | ✔     |         |          |
| CRUX                             | ✔       | ✔       |       | ✔     |         |          |
| Cygwin                           | ✔       | ✔       | ✔     |       |         |          |
| Debian, Ubuntu, other deb-based  |         | ✔       | ✔     | ✔     |         |          |
| DistroWatch.com                  | ✔       |         |       | ✔     |         | ✔        |
| Exherbo                          |         |         | ✔     |       |         |          |
| F-Droid                          |         |         | ✔     | ✔     | ✔       |          |
| FreeBSD                          | ✔       | ✔       | ✔     | ✔     |         |          |
| freshcode.club                   | ✔       |         |       | ✔     | ✔       |          |
| Gentoo, Funtoo                   | ✔       | ✔       | ✔     | ✔     | ✔ (1)   | ✔ (1)    |
| Guix                             | ✔       |         |       | ✔     | ✔       |          |
| GoboLinux                        | ✔       |         |       | ✔     | ✔       |          |
| Hackage                          | ✔       | ✔ (3)   | ✔     | ✔     | ✔       |          |
| HaikuPorts                       |         |         | ✔     |       |         |          |
| Homebrew                         | ✔       |         |       | ✔     |         |          |
| HP-UX                            |         |         |       |       |         |          |
| just-install                     |         |         |       |       |         | ✔        |
| KaOS                             |         |         |       |       |         |          |
| Linuxbrew                        | ✔       |         |       | ✔     |         |          |
| LuaRocks                         |         |         |       |       |         |          |
| MacPorts                         | ✔       | ✔       | ✔     | ✔     | ✔       |          |
| MSYS2                            | ✔       | ✔       | ✔     | ✔     | ✔       |          |
| MX Linux                         |         | ✔       | ✔     | ✔     |         |          |
| nixpkgs                          | ✔       | ✔       |       | ✔     | ✔       |          |
| Npackd                           | ✔       |         | ✔     | ✔     | ✔       | ✔        |
| OpenBSD                          | ✔       | ✔       | ✔     |       |         |          |
| OpenIndiana                      | ✔       |         | ✔     | ✔     |         | ✔        |
| OpenMandriva                     | ✔       | ✔       | ✔     | ✔     | ✔       |          |
| OpenPKG                          | ✔       |         | ✔     | ✔     | ✔       | ✔        |
| OS4Depot                         | ✔       |         | ✔     |       |         |          |
| PCLinuxOS                        | ✔       | ✔       | ✔     |       |         |          |
| Pisi                             | ✔       | ✔       | ✔     | ✔     | ✔       | ✔        |
| pkgsrc                           | ✔       | ✔       | ✔     |       |         |          |
| PyPi                             | ✔       |         |       | ✔ (2) |         |          |
| PLD                              |         |         |       |       |         |          |
| Ravenports                       | ✔       |         | ✔     | ✔     |         |          |
| ReactOS rapps                    | ✔       |         |       | ✔     | ✔       | ✔        |
| RubyGems                         |         |         |       | ✔ (2) |         |          |
| Rudix                            | ✔       |         |       |       | ✔       |          |
| Salix                            | ✔       |         |       |       |         |          |
| Scoop                            |         |         |       | ✔     | ✔       | ✔        |
| SlackBuilds                      |         | ✔ (3)   | ✔     | ✔     |         | ✔        |
| Slackware                        |         |         |       |       |         |          |
| SliTaz                           | ✔       |         | ✔     | ✔     |         |          |
| Solus                            | ✔       | ✔       | ✔     |       | ✔       |          |
| Stackage                         | ✔       |         |       |       |         |          |
| T2 SDE                           | ✔       | ✔       | ✔     | ✔     | ✔       | ✔        |
| Termux                           | ✔       |         |       | ✔     |         | ✔        |
| Vcpkg                            | ✔       |         |       | ✔     |         |          |
| Void                             | ✔       | ✔       |       | ✔     | ✔       |          |
| Wikidata                         | ✔       |         |       | ✔     | ✔       |          |
| YACP                             | ✔       |         | ✔     |       |         |          |

(1) Gentoo support is not complete, complex cases like conditional downloads and licenses
are ignored for now.

(2) WWWs are autogenerated for upstream package repos like CPAN, PyPi

(3) It's common to obfuscate maintainer emails in Hackage and SlackBuilds. Obfuscated emails are ignored.

## Documentation

- How to [run](docs/RUNNING.md) repology tools on your own
- How to extend or fix [rules](https://github.com/repology/repology-rules/blob/master/README.md) for package matching
- How repology [compares versions](https://github.com/repology/libversion/blob/master/doc/ALGORITHM.md)

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
