from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar, Iterable, Mapping, Optional, Union

DESCRIPTOR: _descriptor.FileDescriptor

class Build(_message.Message):
    __slots__ = ["ack_missing_dwarf", "build_step", "cbuilder", "cherry_pick", "cmakebuilder", "dep", "extra_file", "gobuilder", "gomodbuilder", "hash", "in_tree_build", "install", "mesonbuilder", "perlbuilder", "pull", "pythonbuilder", "runtime_dep", "runtime_union", "source", "split_package", "version", "writable_sourcedir"]
    ACK_MISSING_DWARF_FIELD_NUMBER: ClassVar[int]
    BUILD_STEP_FIELD_NUMBER: ClassVar[int]
    CBUILDER_FIELD_NUMBER: ClassVar[int]
    CHERRY_PICK_FIELD_NUMBER: ClassVar[int]
    CMAKEBUILDER_FIELD_NUMBER: ClassVar[int]
    DEP_FIELD_NUMBER: ClassVar[int]
    EXTRA_FILE_FIELD_NUMBER: ClassVar[int]
    GOBUILDER_FIELD_NUMBER: ClassVar[int]
    GOMODBUILDER_FIELD_NUMBER: ClassVar[int]
    HASH_FIELD_NUMBER: ClassVar[int]
    INSTALL_FIELD_NUMBER: ClassVar[int]
    IN_TREE_BUILD_FIELD_NUMBER: ClassVar[int]
    MESONBUILDER_FIELD_NUMBER: ClassVar[int]
    PERLBUILDER_FIELD_NUMBER: ClassVar[int]
    PULL_FIELD_NUMBER: ClassVar[int]
    PYTHONBUILDER_FIELD_NUMBER: ClassVar[int]
    RUNTIME_DEP_FIELD_NUMBER: ClassVar[int]
    RUNTIME_UNION_FIELD_NUMBER: ClassVar[int]
    SOURCE_FIELD_NUMBER: ClassVar[int]
    SPLIT_PACKAGE_FIELD_NUMBER: ClassVar[int]
    VERSION_FIELD_NUMBER: ClassVar[int]
    WRITABLE_SOURCEDIR_FIELD_NUMBER: ClassVar[int]
    ack_missing_dwarf: str
    build_step: _containers.RepeatedCompositeFieldContainer[BuildStep]
    cbuilder: CBuilder
    cherry_pick: _containers.RepeatedScalarFieldContainer[str]
    cmakebuilder: CMakeBuilder
    dep: _containers.RepeatedScalarFieldContainer[str]
    extra_file: _containers.RepeatedScalarFieldContainer[str]
    gobuilder: GoBuilder
    gomodbuilder: GomodBuilder
    hash: str
    in_tree_build: bool
    install: Install
    mesonbuilder: MesonBuilder
    perlbuilder: PerlBuilder
    pull: Pull
    pythonbuilder: PythonBuilder
    runtime_dep: _containers.RepeatedScalarFieldContainer[str]
    runtime_union: _containers.RepeatedCompositeFieldContainer[Union]
    source: str
    split_package: _containers.RepeatedCompositeFieldContainer[SplitPackage]
    version: str
    writable_sourcedir: bool
    def __init__(self, source: Optional[str] = ..., pull: Optional[Union[Pull, Mapping]] = ..., hash: Optional[str] = ..., version: Optional[str] = ..., extra_file: Optional[Iterable[str]] = ..., cherry_pick: Optional[Iterable[str]] = ..., writable_sourcedir: bool = ..., in_tree_build: bool = ..., ack_missing_dwarf: Optional[str] = ..., dep: Optional[Iterable[str]] = ..., build_step: Optional[Iterable[Union[BuildStep, Mapping]]] = ..., cbuilder: Optional[Union[CBuilder, Mapping]] = ..., cmakebuilder: Optional[Union[CMakeBuilder, Mapping]] = ..., mesonbuilder: Optional[Union[MesonBuilder, Mapping]] = ..., perlbuilder: Optional[Union[PerlBuilder, Mapping]] = ..., pythonbuilder: Optional[Union[PythonBuilder, Mapping]] = ..., gomodbuilder: Optional[Union[GomodBuilder, Mapping]] = ..., gobuilder: Optional[Union[GoBuilder, Mapping]] = ..., runtime_dep: Optional[Iterable[str]] = ..., install: Optional[Union[Install, Mapping]] = ..., split_package: Optional[Iterable[Union[SplitPackage, Mapping]]] = ..., runtime_union: Optional[Iterable[Union[Union, Mapping]]] = ...) -> None: ...

class BuildStep(_message.Message):
    __slots__ = ["argv"]
    ARGV_FIELD_NUMBER: ClassVar[int]
    argv: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, argv: Optional[Iterable[str]] = ...) -> None: ...

class CBuilder(_message.Message):
    __slots__ = ["autoreconf", "extra_configure_flag", "extra_ldflag", "extra_make_flag"]
    AUTORECONF_FIELD_NUMBER: ClassVar[int]
    EXTRA_CONFIGURE_FLAG_FIELD_NUMBER: ClassVar[int]
    EXTRA_LDFLAG_FIELD_NUMBER: ClassVar[int]
    EXTRA_MAKE_FLAG_FIELD_NUMBER: ClassVar[int]
    autoreconf: bool
    extra_configure_flag: _containers.RepeatedScalarFieldContainer[str]
    extra_ldflag: _containers.RepeatedScalarFieldContainer[str]
    extra_make_flag: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, extra_configure_flag: Optional[Iterable[str]] = ..., extra_make_flag: Optional[Iterable[str]] = ..., autoreconf: bool = ..., extra_ldflag: Optional[Iterable[str]] = ...) -> None: ...

class CMakeBuilder(_message.Message):
    __slots__ = ["extra_cmake_flag"]
    EXTRA_CMAKE_FLAG_FIELD_NUMBER: ClassVar[int]
    extra_cmake_flag: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, extra_cmake_flag: Optional[Iterable[str]] = ...) -> None: ...

class Claim(_message.Message):
    __slots__ = ["dir", "glob"]
    DIR_FIELD_NUMBER: ClassVar[int]
    GLOB_FIELD_NUMBER: ClassVar[int]
    dir: str
    glob: str
    def __init__(self, glob: Optional[str] = ..., dir: Optional[str] = ...) -> None: ...

class GoBuilder(_message.Message):
    __slots__ = ["go_env", "import_path", "install"]
    GO_ENV_FIELD_NUMBER: ClassVar[int]
    IMPORT_PATH_FIELD_NUMBER: ClassVar[int]
    INSTALL_FIELD_NUMBER: ClassVar[int]
    go_env: _containers.RepeatedScalarFieldContainer[str]
    import_path: str
    install: str
    def __init__(self, install: Optional[str] = ..., import_path: Optional[str] = ..., go_env: Optional[Iterable[str]] = ...) -> None: ...

class GomodBuilder(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Install(_message.Message):
    __slots__ = ["capability", "chmod", "delete", "empty_dir", "file", "rename", "symlink", "systemd_unit"]
    class Cap(_message.Message):
        __slots__ = ["capability", "filename"]
        CAPABILITY_FIELD_NUMBER: ClassVar[int]
        FILENAME_FIELD_NUMBER: ClassVar[int]
        capability: str
        filename: str
        def __init__(self, capability: Optional[str] = ..., filename: Optional[str] = ...) -> None: ...
    class Chmod(_message.Message):
        __slots__ = ["name", "setuid"]
        NAME_FIELD_NUMBER: ClassVar[int]
        SETUID_FIELD_NUMBER: ClassVar[int]
        name: str
        setuid: bool
        def __init__(self, setuid: bool = ..., name: Optional[str] = ...) -> None: ...
    class File(_message.Message):
        __slots__ = ["destpath", "srcpath"]
        DESTPATH_FIELD_NUMBER: ClassVar[int]
        SRCPATH_FIELD_NUMBER: ClassVar[int]
        destpath: str
        srcpath: str
        def __init__(self, srcpath: Optional[str] = ..., destpath: Optional[str] = ...) -> None: ...
    class Rename(_message.Message):
        __slots__ = ["newname", "oldname"]
        NEWNAME_FIELD_NUMBER: ClassVar[int]
        OLDNAME_FIELD_NUMBER: ClassVar[int]
        newname: str
        oldname: str
        def __init__(self, oldname: Optional[str] = ..., newname: Optional[str] = ...) -> None: ...
    class Symlink(_message.Message):
        __slots__ = ["newname", "oldname"]
        NEWNAME_FIELD_NUMBER: ClassVar[int]
        OLDNAME_FIELD_NUMBER: ClassVar[int]
        newname: str
        oldname: str
        def __init__(self, oldname: Optional[str] = ..., newname: Optional[str] = ...) -> None: ...
    CAPABILITY_FIELD_NUMBER: ClassVar[int]
    CHMOD_FIELD_NUMBER: ClassVar[int]
    DELETE_FIELD_NUMBER: ClassVar[int]
    EMPTY_DIR_FIELD_NUMBER: ClassVar[int]
    FILE_FIELD_NUMBER: ClassVar[int]
    RENAME_FIELD_NUMBER: ClassVar[int]
    SYMLINK_FIELD_NUMBER: ClassVar[int]
    SYSTEMD_UNIT_FIELD_NUMBER: ClassVar[int]
    capability: _containers.RepeatedCompositeFieldContainer[Install.Cap]
    chmod: _containers.RepeatedCompositeFieldContainer[Install.Chmod]
    delete: _containers.RepeatedScalarFieldContainer[str]
    empty_dir: _containers.RepeatedScalarFieldContainer[str]
    file: _containers.RepeatedCompositeFieldContainer[Install.File]
    rename: _containers.RepeatedCompositeFieldContainer[Install.Rename]
    symlink: _containers.RepeatedCompositeFieldContainer[Install.Symlink]
    systemd_unit: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, systemd_unit: Optional[Iterable[str]] = ..., symlink: Optional[Iterable[Union[Install.Symlink, Mapping]]] = ..., empty_dir: Optional[Iterable[str]] = ..., chmod: Optional[Iterable[Union[Install.Chmod, Mapping]]] = ..., capability: Optional[Iterable[Union[Install.Cap, Mapping]]] = ..., file: Optional[Iterable[Union[Install.File, Mapping]]] = ..., rename: Optional[Iterable[Union[Install.Rename, Mapping]]] = ..., delete: Optional[Iterable[str]] = ...) -> None: ...

class MesonBuilder(_message.Message):
    __slots__ = ["extra_meson_flag"]
    EXTRA_MESON_FLAG_FIELD_NUMBER: ClassVar[int]
    extra_meson_flag: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, extra_meson_flag: Optional[Iterable[str]] = ...) -> None: ...

class PerlBuilder(_message.Message):
    __slots__ = ["extra_makefile_flag"]
    EXTRA_MAKEFILE_FLAG_FIELD_NUMBER: ClassVar[int]
    extra_makefile_flag: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, extra_makefile_flag: Optional[Iterable[str]] = ...) -> None: ...

class Pull(_message.Message):
    __slots__ = ["debian_packages", "force_semver", "release_regexp", "release_replace_all", "releases_url"]
    DEBIAN_PACKAGES_FIELD_NUMBER: ClassVar[int]
    FORCE_SEMVER_FIELD_NUMBER: ClassVar[int]
    RELEASES_URL_FIELD_NUMBER: ClassVar[int]
    RELEASE_REGEXP_FIELD_NUMBER: ClassVar[int]
    RELEASE_REPLACE_ALL_FIELD_NUMBER: ClassVar[int]
    debian_packages: str
    force_semver: bool
    release_regexp: str
    release_replace_all: RegexpReplaceAll
    releases_url: str
    def __init__(self, debian_packages: Optional[str] = ..., releases_url: Optional[str] = ..., release_regexp: Optional[str] = ..., release_replace_all: Optional[Union[RegexpReplaceAll, Mapping]] = ..., force_semver: bool = ...) -> None: ...

class PythonBuilder(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class RegexpReplaceAll(_message.Message):
    __slots__ = ["expr", "repl"]
    EXPR_FIELD_NUMBER: ClassVar[int]
    REPL_FIELD_NUMBER: ClassVar[int]
    expr: str
    repl: str
    def __init__(self, expr: Optional[str] = ..., repl: Optional[str] = ...) -> None: ...

class SplitPackage(_message.Message):
    __slots__ = ["claim", "name", "runtime_dep"]
    CLAIM_FIELD_NUMBER: ClassVar[int]
    NAME_FIELD_NUMBER: ClassVar[int]
    RUNTIME_DEP_FIELD_NUMBER: ClassVar[int]
    claim: _containers.RepeatedCompositeFieldContainer[Claim]
    name: str
    runtime_dep: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: Optional[str] = ..., claim: Optional[Iterable[Union[Claim, Mapping]]] = ..., runtime_dep: Optional[Iterable[str]] = ...) -> None: ...

class Union(_message.Message):
    __slots__ = ["dir", "pkg"]
    DIR_FIELD_NUMBER: ClassVar[int]
    PKG_FIELD_NUMBER: ClassVar[int]
    dir: str
    pkg: str
    def __init__(self, dir: Optional[str] = ..., pkg: Optional[str] = ...) -> None: ...
