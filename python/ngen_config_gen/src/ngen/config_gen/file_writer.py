from typing import Callable, Protocol, Union
from typing_extensions import Literal
from pathlib import Path
from tempfile import NamedTemporaryFile
import warnings
import hashlib

from pydantic import BaseModel
from ngen.init_config.serializer import (
    IniSerializer,
    JsonSerializer,
    NamelistSerializer,
    TomlSerializer,
    YamlSerializer,
)


class FileWriter(Protocol):
    def __call__(self, id: Union[str, Literal["global"]], data: BaseModel):
        ...


class _Reader(Protocol):
    """
    `read()` at most `size` bytes _or_ unicode code points.
    EOF is empty bytes buffer of empty str.
    """

    def read(self, size: Union[int, None] = ...) -> Union[bytes, str]:
        ...


def _sha256_hexdigest(r: _Reader) -> str:
    hash = hashlib.sha256()

    chunk_size = 8192
    while chunk := r.read(chunk_size):
        if isinstance(chunk, str):
            # assume utf-8; this could fail
            chunk = chunk.encode("utf-8")
        hash.update(chunk)

    return hash.hexdigest()


class DefaultFileWriter:
    def __init__(self, root: Union[str, Path]):
        root = Path(root)
        if not root.exists():
            root.mkdir(parents=True)
        elif root.is_file():
            raise FileExistsError(f'expected dir got file: "{root!s}"')
        self.__root = root

    @staticmethod
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
        elif isinstance(data, BaseModel):  # type: ignore
            json_serializer(data)

        raise RuntimeError(f'unaccepted type: "{type(data)}"')

    @staticmethod
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
        elif isinstance(data, BaseModel):  # type: ignore
            return "json"

        raise RuntimeError(f'unaccepted type: "{type(data)}"')

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

    def __call__(self, id: Union[str, Literal["global"]], data: BaseModel):
        class_name = data.__class__.__name__
        ext = DefaultFileWriter._get_file_extension(data)
        output_file = self.__root / f"{class_name}_{id}.{ext}"

        serializer = DefaultFileWriter._get_serializer(data)

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
