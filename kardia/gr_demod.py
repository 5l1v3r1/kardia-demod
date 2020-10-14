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
import math

from gnuradio import filter, analog, gr, blocks, zeromq
from gnuradio.filter import firdes

KARDIA_FM_CFREQ = 19000  # Hz
FM_DEVIATION = 300  # Hz

KARDIA_MOD_RANGE = 1000  # Hz
FILTER_TRANS_WIDTH = 100  # Hz
FREQ_TRANS_LP_CUTOFF = 2000  # Hz


class DemodBlock(gr.hier_block2):

    def __init__(self, samp_rate):
        super().__init__('KardiaDemodBlock',
                         gr.io_signature(1, 1, gr.sizeof_float),
                         gr.io_signature(1, 1, gr.sizeof_float))

        self.samp_rate = samp_rate

        self.input_bp_fil = self._design_input_bandpass()
        self.freq_trans_fil = self._design_freq_trans_filter()
        self.freq_trans_out_lp_fil = self._design_freq_trans_out_lp()
        self.fm_demod = self._design_freq_demod()

        self.connect(self, self.input_bp_fil)
        self.connect(self.input_bp_fil, self.freq_trans_fil)
        self.connect(self.freq_trans_fil, self.freq_trans_out_lp_fil)
        self.connect(self.freq_trans_out_lp_fil, self.fm_demod)
        self.connect(self.fm_demod, self)

    def _design_input_bandpass(self):
        gain = 1
        lowcut = KARDIA_FM_CFREQ - KARDIA_MOD_RANGE
        highcut = KARDIA_FM_CFREQ + KARDIA_MOD_RANGE
        trans_width = FILTER_TRANS_WIDTH

        bp_taps = firdes.band_pass(gain, self.samp_rate, lowcut, highcut, trans_width)
        bp_filter = filter.fir_filter_fff(decimation=1, taps=bp_taps)
        return bp_filter

    def _design_freq_trans_filter(self):
        decimation = 1
        taps = [1]
        cfreq = KARDIA_FM_CFREQ

        freq_filter = filter.freq_xlating_fir_filter_fcf(decimation, taps, cfreq, self.samp_rate)
        return freq_filter

    def _design_freq_trans_out_lp(self):
        gain = 1
        cutoff = FREQ_TRANS_LP_CUTOFF
        trans_width = FILTER_TRANS_WIDTH

        fil_taps = firdes.low_pass(gain, self.samp_rate, cutoff, trans_width)
        lp_filter = filter.fir_filter_ccf(decimation=1, taps=fil_taps)
        return lp_filter

    def _design_freq_demod(self):
        gain = self.samp_rate / (2 * math.pi * FM_DEVIATION / 8.0)
        demod = analog.quadrature_demod_cf(gain)
        return demod


class Demodulator(gr.top_block):

    def __init__(self, samp_rate):
        super().__init__('KardiaDemodulator')
        self._samp_rate = samp_rate

        self.source = None
        self.demod_block = DemodBlock(samp_rate)
        self.sink = None

    def _set_source_block(self, blk):
        if self.source is not None:
            self.disconnect(self.source, self.demod_block)

        self.source = blk
        self.connect(blk, self.demod_block)

    def _set_sink_block(self, blk):
        if self.sink is not None:
            self.disconnect(self.demod_block, self.sink)

        self.sink = blk
        self.connect(self.demod_block, blk)

    def set_wav_source(self, fpath):
        blk = blocks.wavfile_source(fpath)
        self._set_source_block(blk)
        return blk

    def set_float32_source(self, fpath):
        blk = blocks.file_source(gr.sizeof_float, fpath)
        self._set_source_block(blk)
        return blk

    def set_float32_sink(self, fpath):
        blk = blocks.file_sink(gr.sizeof_float, fpath)
        self._set_sink_block(blk)
        return blk

    def set_vector_sink(self):
        blk = blocks.vector_sink_f()
        self._set_sink_block(blk)
        return blk

    def set_zmq_sink(self, url):
        zmq_sink = zeromq.push_sink(gr.sizeof_float, 1, url)
        self._set_sink_block(zmq_sink)
        return zmq_sink
