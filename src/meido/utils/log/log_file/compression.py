import datetime
import os
import shutil
from collections.abc import Callable
from functools import partial
from typing import Optional

from meido.utils.log._ctime import get_ctime
from meido.utils.log.log_file._datetime import aware_now

__all__ = ("Compression",)


class FileDateFormatter:
    def __init__(self, _datetime: datetime.datetime | None = None) -> None:
        self.datetime = _datetime or aware_now()

    def __format__(self, spec: str) -> str:
        if not spec:
            spec = "%Y-%m-%d_%H-%M-%S_%f"
        return self.datetime.__format__(spec)


def generate_rename_path(root, ext, creation_time):
    creation_datetime = datetime.datetime.fromtimestamp(creation_time)
    date = FileDateFormatter(creation_datetime)

    renamed_path = "{}.{}{}".format(root, date, ext)
    counter = 1

    while os.path.exists(renamed_path):
        counter += 1
        renamed_path = "{}.{}.{}{}".format(root, date, counter, ext)

    return renamed_path


class Compression:
    _compression: Optional[Callable] = None

    def __init__(self, compression: str | Callable | None) -> None:
        if isinstance(compression, str):
            ext = compression.strip().lstrip(".")

            match ext:
                case "gz":
                    import gzip

                    compress = partial(Compression.copy_compress, opener=gzip.open, mode="wb")
                case "bz2":
                    import bz2

                    compress = partial(Compression.copy_compress, opener=bz2.open, mode="wb")

                case "xz":
                    import lzma

                    compress = partial(Compression.copy_compress, opener=lzma.open, mode="wb", format=lzma.FORMAT_XZ)

                case "lzma":
                    import lzma

                    compress = partial(Compression.copy_compress, opener=lzma.open, mode="wb", format=lzma.FORMAT_ALONE)

                case "tar":
                    import tarfile

                    compress = partial(Compression.add_compress, opener=tarfile.open, mode="w:")

                case "tar.gz":
                    import gzip
                    import tarfile

                    compress = partial(Compression.add_compress, opener=tarfile.open, mode="w:gz")

                case "tar.bz2":
                    import bz2
                    import tarfile

                    compress = partial(Compression.add_compress, opener=tarfile.open, mode="w:bz2")

                case "tar.xz":
                    import lzma
                    import tarfile

                    compress = partial(Compression.add_compress, opener=tarfile.open, mode="w:xz")

                case "zip":
                    import zipfile

                    compress = partial(
                        Compression.write_compress,
                        opener=zipfile.ZipFile,
                        mode="w",
                        compression=zipfile.ZIP_DEFLATED,
                    )
                case _:
                    raise ValueError("Invalid compression format: '%s'" % ext)
            self._compression = partial(Compression.compression, ext="." + ext, compress_function=compress)
        elif callable(compression):
            self._compression = compression
        else:
            raise TypeError("Cannot infer compression for objects of type: '%s'" % type(compression).__name__)

    def __call__(self, *args, **kwargs):
        if self._compression is not None:
            return self._compression(*args, **kwargs)

    @staticmethod
    def add_compress(path_in, path_out, opener, **kwargs):
        with opener(path_out, **kwargs) as f_comp:
            f_comp.add(path_in, os.path.basename(path_in))

    @staticmethod
    def write_compress(path_in, path_out, opener, **kwargs):
        with opener(path_out, **kwargs) as f_comp:
            f_comp.write(path_in, os.path.basename(path_in))

    @staticmethod
    def copy_compress(path_in, path_out, opener, **kwargs):
        with open(path_in, "rb") as f_in:
            with opener(path_out, **kwargs) as f_out:
                shutil.copyfileobj(f_in, f_out)

    @staticmethod
    def compression(path_in, ext, compress_function):
        path_out = "{}{}".format(path_in, ext)

        if os.path.exists(path_out):
            creation_time = get_ctime(path_out)
            root, ext_before = os.path.splitext(path_in)
            renamed_path = generate_rename_path(root, ext_before + ext, creation_time)
            os.rename(path_out, renamed_path)
        compress_function(path_in, path_out)
        os.remove(path_in)
