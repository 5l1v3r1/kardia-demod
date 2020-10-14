# kardia demod
# Copyright (C) 2020  Lukas Magel

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import struct
from io import SEEK_SET, SEEK_CUR
from typing import BinaryIO


def unpack(args):
    if len(args) == 1:
        return args[0]
    return args


class FileIOBase:

    def __init__(self, fp: BinaryIO):
        if not fp.seekable():
            raise ValueError('IO object must be seekable')

        self._fp = fp

    def _tell(self) -> int:
        return self._fp.tell()

    def _read(self, s: int) -> bytes:
        r = self._fp.read(s)
        if len(r) < s:
            raise IOError('Read beyond EOF')

        return r

    def _seek(self, off: int = 0) -> None:
        self._fp.seek(off, SEEK_SET)

    def _seek_relative(self, off: int = 0) -> None:
        self._fp.seek(off, SEEK_CUR)

    def _read_packed(self, fmt: str) -> any:
        s = struct.calcsize(fmt)
        val_bin = self._read(s)

        args = struct.unpack(fmt, val_bin)
        return unpack(args)
