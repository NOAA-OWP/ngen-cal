import json
import tarfile
import tempfile

import pydantic
import pytest

from ngen.config_gen.file_writer import Compression, TarFileWriter


class Foo(pydantic.BaseModel):
    bar: int


@pytest.mark.parametrize("compression", [c for c in Compression])
def test_write_single(compression: Compression):
    with tempfile.NamedTemporaryFile() as file:
        id = "42"
        data = Foo(bar=42)
        try:
            with TarFileWriter(file.name, compression=compression) as writer:
                writer(id, data)
        except tarfile.CompressionError as e:
            pytest.xfail(reason=str(e))

        assert tarfile.is_tarfile(file.name)
        with tarfile.open(file.name, f"r:{compression.extension()}") as f:
            members = f.getmembers()
            assert len(members) == 1
            member = members[0]
            assert member.isfile()

            buff = f.extractfile(member)
            assert buff is not None
            d = json.load(buff)
            assert d == json.loads(data.json())


@pytest.mark.parametrize("compression", [c for c in Compression])
def test_write_multiple(compression: Compression):
    with tempfile.NamedTemporaryFile() as file:
        data = {"42": Foo(bar=42), "12": Foo(bar=12)}
        try:
            with TarFileWriter(file.name, compression=compression) as writer:
                for id, item in data.items():
                    writer(id, item)
        except tarfile.CompressionError as e:
            pytest.xfail(reason=str(e))

        assert tarfile.is_tarfile(file.name)
        with tarfile.open(file.name, f"r:{compression.extension()}") as f:
            members = f.getmembers()
            assert len(members) == 2


@pytest.mark.parametrize("compression", [c for c in Compression])
def test_overriting_file_warns(compression: Compression):
    with tempfile.NamedTemporaryFile() as file:
        id = "42"
        data = Foo(bar=42)
        try:
            with TarFileWriter(file.name, compression=compression) as writer:
                writer(id, data)
                with pytest.warns():
                    writer(id, data)
        except tarfile.CompressionError as e:
            pytest.xfail(reason=str(e))
