#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

''' Using overlapping '''

import numpy as np
import pywt
import logging

import minimal
from stereo_MST_coding_32 import Stereo_MST_Coding_32 as Stereo_Coding

from temporal_no_overlapped_DWT_coding import Temporal_No_Overlapped_DWT
import math

class Temporal_Overlapped_DWT(Temporal_No_Overlapped_DWT):
    
    def __init__(self):
        super().__init__()
        logging.info(__doc__) 
        self.chunks = [self.generate_zero_chunk(), self.generate_zero_chunk(), self.generate_zero_chunk()]
        overlaped_area_size = self.max_filters_length * (1 << self.dwt_levels)
        self.overlaped_area_size = 1<<math.ceil(math.log(overlaped_area_size)/math.log(2))
        self.overlaped_area_size = 0

        zero_array = np.zeros(shape=minimal.args.frames_per_chunk+self.overlaped_area_size*2)
        coeffs = pywt.wavedec(zero_array, wavelet=self.wavelet, level=self.dwt_levels, mode="per")
        self.slices = pywt.coeffs_to_array(coeffs)[1]
        self.shapes = pywt.ravel_coeffs(coeffs)[2]
        logging.info(f"shapes")

    def analyze(self, chunk):
        self.chunks[0] = self.chunks[1]
        self.chunks[1] = self.chunks[2]
        self.chunks[2] = chunk

        extended_chunk = np.concatenate((self.chunks[0][-self.overlaped_area_size:],self.chunks[1],self.chunks[2][self.overlaped_area_size:]))

        DWT_extended_chunk = super().analyze(extended_chunk)
        #DWT_extended_chunk = super().analyze(chunk)

        DWT_chunk = np.empty((minimal.args.frames_per_chunk, self.NUMBER_OF_CHANNELS), dtype=np.int32) #this is an empty chunk (numpy array)

        subband_size = pywt.wavedecn_shapes((DWT_extended_chunk.length,), wavelet='db2', level=3, mode='per')
        
        subband_middle_parts = []

        #I don't really know how we should do it with a for loop
        #levels = 3
        # for l in range(levels):
        #     subband_middle_parts.append(DWT_extended_chunk[self.overlaped_area_size/math.pow(2,l):])

        #...so I'm going to do it like this:
        subband_l2_h2 = DWT_extended_chunk[:len(DWT_extended_chunk)/2]
        subband_l2 = subband_l2_h2[:len(subband_l2_h2)/2]
        subband_h2 = subband_l2_h2[len(subband_l2_h2)/2:]
        subband_h1 = DWT_extended_chunk[len(DWT_extended_chunk)/2:]

        subband_middle_parts.append(subband_l2[len(subband_l2)/4:len(subband_l2)*3/4])
        subband_middle_parts.append(subband_h2[len(subband_h2)/4:len(subband_h2)*3/4])
        subband_middle_parts.append(subband_h1[len(subband_h1)/4:len(subband_h1)*3/4])

        return np.concatenate(subband_middle_parts)

    def synthesize(self, chunk_DWT):
        '''Inverse DWT.'''
        # chunk = np.empty((minimal.args.frames_per_chunk, self.NUMBER_OF_CHANNELS), dtype=np.int32)
        # for c in range(self.NUMBER_OF_CHANNELS):
        #     channel_coeffs = pywt.array_to_coeffs(chunk_DWT[:, c], self.slices, output_format="wavedec")
        #     #chunk[:, c] = np.rint(pywt.waverec(channel_coeffs, wavelet=self.wavelet, mode="per")).astype(np.int32)
        #     chunk[:, c] = pywt.waverec(channel_coeffs, wavelet=self.wavelet, mode="per")
        # chunk = super().synthesize(chunk)
        return super().synthesize(chunk_DWT)

from temporal_no_overlapped_DWT_coding import Temporal_No_Overlapped_DWT__verbose

class Temporal_Overlapped_DWT__verbose(Temporal_No_Overlapped_DWT__verbose):
    pass

try:
    import argcomplete  # <tab> completion for argparse.
except ImportError:
    logging.warning("Unable to import argcomplete (optional)")

if __name__ == "__main__":
    minimal.parser.description = __doc__
    try:
        argcomplete.autocomplete(minimal.parser)
    except Exception:
        logging.warning("argcomplete not working :-/")
    minimal.args = minimal.parser.parse_known_args()[0]
    if minimal.args.show_stats or minimal.args.show_samples:
        intercom = Temporal_Overlapped_DWT__verbose()
    else:
        intercom = Temporal_Overlapped_DWT()
    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        intercom.print_final_averages()