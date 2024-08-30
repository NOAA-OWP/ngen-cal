from __future__ import annotations

import dataclasses
import enum
import hashlib
import io
import tarfile
import warnings
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Protocol, Union

from ngen.init_config.serializer import (
    IniSerializer,
    JsonSerializer,
    NamelistSerializer,
    TomlSerializer,
    YamlSerializer,
    GenericSerializer,
)
from pydantic import BaseModel
from typing_extensions import Literal, Self


class FileWriter(Protocol):
    def __call__(self, id: str | Literal["global"], data: BaseModel): ...


class _Reader(Protocol):
    """
    `read()` at most `size` bytes _or_ unicode code points.
    EOF is empty bytes buffer of empty str.
    """

    def read(self, size: int | None = ...) -> bytes | str: ...


def _sha256_hexdigest(r: _Reader) -> str:
    hash = hashlib.sha256()

    chunk_size = 8192
    while chunk := r.read(chunk_size):
        if isinstance(chunk, str):
            # assume utf-8; this could fail
            chunk = chunk.encode("utf-8")
        hash.update(chunk)

    return hash.hexdigest()


def _get_str_serializer(data: BaseModel) -> Callable[[], str]:
    if isinstance(data, IniSerializer):
        return data.to_ini_str
    elif isinstance(data, JsonSerializer):
        return data.to_json_str
    elif isinstance(data, NamelistSerializer):
        return data.to_namelist_str
    elif isinstance(data, TomlSerializer):
        return data.to_toml_str
    elif isinstance(data, YamlSerializer):
        return data.to_yaml_str
    elif isinstance(data, GenericSerializer):
        return data.to_str
    elif isinstance(data, BaseModel):
        return data.json

    raise RuntimeError(f'unaccepted type: "{type(data)}"')


def _get_serializer(data: BaseModel) -> Callable[[Path], None]:
    def json_serializer(m: BaseModel):
        def serialize(p: Path):
            p.write_text(m.json())

        return serialize

    if isinstance(data, IniSerializer):
        return data.to_ini
    elif isinstance(data, JsonSerializer):
        return data.to_json
    elif isinstance(data, NamelistSerializer):
        return data.to_namelist
    elif isinstance(data, TomlSerializer):
        return data.to_toml
    elif isinstance(data, YamlSerializer):
        return data.to_yaml
    elif isinstance(data, GenericSerializer):
        return data.to_file
    elif isinstance(data, BaseModel):  # type: ignore
        json_serializer(data)

    raise RuntimeError(f'unaccepted type: "{type(data)}"')


def _get_file_extension(data: BaseModel) -> str:
    if isinstance(data, IniSerializer):
        return "ini"
    elif isinstance(data, JsonSerializer):
        return "json"
    elif isinstance(data, NamelistSerializer):
        return "namelist"
    elif isinstance(data, TomlSerializer):
        return "toml"
    elif isinstance(data, YamlSerializer):
        return "yaml"
    elif isinstance(data, GenericSerializer):
        return ""
    elif isinstance(data, BaseModel):  # type: ignore
        return "json"

    raise RuntimeError(f'unaccepted type: "{type(data)}"')


class DefaultFileWriter:
    def __init__(self, root: str | Path):
        root = Path(root)
        if not root.exists():
            root.mkdir(parents=True)
        elif root.is_file():
            raise FileExistsError(f'expected dir got file: "{root!s}"')
        self.__root = root

    @staticmethod
    def _gen_alt_filename(p: Path) -> Path:
        stem = p.stem
        ext = p.suffix
        f_name = p
        i = 1
        while f_name.exists():
            f_name = p.with_name(f"{stem}_{i:02}{ext}")
            i += 1
        return f_name

    def __call__(self, id: str | Literal["global"], data: BaseModel):
        class_name = data.__class__.__name__
        ext = _get_file_extension(data)
        output_file = self.__root / f"{class_name}_{id}.{ext}"

        serializer = _get_serializer(data)

        # only write when files differ.
        # new file -> write to new file and add a suffix; warn about change
        # files match -> warn that now new file is generated
        if output_file.exists():
            with open(output_file, "rb") as fp:
                exist_digest = _sha256_hexdigest(fp)

            # write new to tmp file and compute its checksum
            with NamedTemporaryFile() as tmp:
                serializer(Path(tmp.name))
                with open(tmp.name, "rb") as fp:
                    new_digest = _sha256_hexdigest(fp)

            if new_digest == exist_digest:
                warnings.warn(
                    f'no new config written; "{output_file!s}" already exists and is identical to generated config'
                )
            else:
                alt_name = DefaultFileWriter._gen_alt_filename(output_file)
                warnings.warn(
                    f'"writing to "{alt_name!s}"; {output_file!s}" already exists'
                )
                output_file = alt_name

        serializer(output_file)


class _Unreachable(Exception): ...


class Compression(enum.Enum):
    UNCOMPRESSED = enum.auto()
    GZIP = enum.auto()
    BZIP2 = enum.auto()
    LZMA = enum.auto()

    def extension(self) -> str:
        if self == Compression.UNCOMPRESSED:
            return ""
        elif self == Compression.GZIP:
            return "gz"
        elif self == Compression.BZIP2:
            return "bz2"
        elif self == Compression.LZMA:
            return "xz"
        raise _Unreachable


@dataclasses.dataclass
class TarFileWriter:
    filepath: Union[str, Path]
    compression: Compression = Compression.GZIP

    def __post_init__(self):
        self.filepath = Path(self.filepath)
        if not self.filepath.exists():
            self.filepath.touch()
        elif not self.filepath.is_file():
            raise FileExistsError(f'expected file got dir: "{self.filepath!s}"')
        self._filehandle: tarfile.TarFile | None = None
        self._open_count: int = 0

    def __enter__(self) -> Self:
        if self._filehandle is None:
            self._filehandle = tarfile.open(
                self.filepath, mode=f"w:{self.compression.extension()}"
            )
        self._open_count += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._open_count -= 1
        if self._open_count < 1:
            assert self._filehandle is not None
            self._filehandle.close()
            self._filehandle = None

    def __call__(self, id: str | Literal["global"], data: BaseModel) -> None:
        class_name = data.__class__.__name__
        ext = _get_file_extension(data)
        output_file = f"{class_name}_{id}.{ext}"
        serializer = _get_str_serializer(data)

        with self:
            assert self._filehandle is not None
            try:
                self._filehandle.getmember(output_file)
                warnings.warn(f'"over-writing existing file {output_file!r}"')
            except KeyError:
                ...
            encoded = serializer().encode()
            buff = io.BytesIO(encoded)
            info = tarfile.TarInfo(name=output_file)
            info.size = len(encoded)
            self._filehandle.addfile(info, fileobj=buff)
