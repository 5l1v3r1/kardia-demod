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

from typing import Tuple, Dict, BinaryIO

import numpy as np

from kardia.util import FileIOBase

FIRST_BLOCK_OFFSET = 0x0C

BLOCK_HEADER_LEN = 0x08
BLOCK_CHECKSUM_LEN = 0x04
FMT_SR_OFFSET = 0x01

FILE_HEADER = b'ALIVE'

FMT_BLOCK_IDENT = b'fmt '
LEAD_IDENTS = {
    1: b'ecg ',
    2: b'ecg2',
    3: b'ecg3',
    4: b'ecg4',
    5: b'ecg5',
    6: b'ecg6',
}


class ATCReader(FileIOBase):

    def __init__(self, fobj: BinaryIO):
        super().__init__(fobj)

        self._blocks = {}

        if not self._check_header():
            raise ValueError('File Header magic string not found')

        self._seek_blocks()

    @property
    def blocks(self) -> Dict[bytes, Tuple[int, int]]:
        return dict(self._blocks)

    def _read_block_header(self) -> Tuple[bytes, int]:
        ident, blen = self._read_packed('<4sI')
        return ident, blen

    def _check_header(self) -> bool:
        self._seek()
        header = self._read(len(FILE_HEADER))

        return header == FILE_HEADER

    def _seek_to_block(self, ident: bytes) -> int:
        if ident not in self._blocks:
            raise IOError('Unknown block: ' + str(ident))
        off, blen = self._blocks[ident]
        self._seek(off + BLOCK_HEADER_LEN)

        return blen

    def _seek_blocks(self) -> None:
        self._seek(FIRST_BLOCK_OFFSET)

        while True:
            cur_off = self._tell()

            try:
                ident, blen = self._read_block_header()
            except IOError:
                break
            self._blocks[ident] = (cur_off, blen)

            # Skip checksum
            self._seek_relative(blen + BLOCK_CHECKSUM_LEN)

    def read_sample_rate(self) -> int:
        self._seek_to_block(FMT_BLOCK_IDENT)
        self._seek_relative(FMT_SR_OFFSET)
        return self._read_packed('<H')

    def read_lead(self, lead_id) -> np.ndarray:
        if lead_id not in LEAD_IDENTS:
            raise ValueError('Unknown lead identifier: ' + str(lead_id))
        lead_ident = LEAD_IDENTS[lead_id]
        blen = self._seek_to_block(lead_ident)

        data_bin = self._read(blen)
        return np.frombuffer(data_bin, np.int16)
