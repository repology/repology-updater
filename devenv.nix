{ pkgs, ... }:
{
  cachix.enable = false;

  packages = [
    pkgs.curl
    pkgs.zstd
    (pkgs.python3.withPackages (p: [
      # requirements.txt
      p.jinja2
      p.pyyaml
      p.brotli
      p.jsonslicer
      p.libversion
      p.lxml
      p.protobuf
      p.psycopg2
      p.pydantic
      p.pyparsing
      p.requests
      p.rubymarshal
      p.tomli
      p.xxhash
      p.yarl
      p.zstandard
      # requirements-dev.txt
      p.flake8
      # TODO: p.flake8-builtins https://github.com/NixOS/nixpkgs/pull/300097
      p.flake8-docstrings
      # TODO: p.flake8-quotes https://github.com/NixOS/nixpkgs/pull/365983
      p.lxml-stubs
      p.mypy
      p.py
      p.pytest
      p.pytest-cov
      p.pytest-datadir
      # TODO: p.pytest-regtest https://github.com/NixOS/nixpkgs/pull/365985
      # TODO: p.types-Jinja2 https://github.com/NixOS/nixpkgs/pull/365989
      p.types-pyyaml
      p.types-protobuf
      p.types-psycopg2
      p.types-requests
      # TODO: p.types-xxhash https://github.com/NixOS/nixpkgs/pull/365989
      p.typing-extensions
      p.voluptuous
      # README.txt
      p.rpm
    ]))
  ];

  scripts = {
    populate.exec = ''
      curl -s https://dumps.repology.org/repology-database-dump-latest.sql.zst \
        | unzstd \
        | psql -U repology
    '';
    update.exec = ''
      ./repology-update.py --fetch --fetch --parse --database --postupdate
    '';
  };

  services.postgres = {
    enable = true;
    extensions = ext: [ ext.pg_libversion ];
    initialScript = ''
      CREATE USER repology PASSWORD 'repology';
      CREATE DATABASE repology OWNER repology;
      \c repology;
      CREATE EXTENSION pg_trgm;
      CREATE EXTENSION libversion;
    '';
  };
}
