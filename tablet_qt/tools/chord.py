#!/usr/bin/python2.7

# http://stackoverflow.com/questions/5173795/how-can-i-generate-a-note-or-chord-in-python  # noqa
# ... and me
# http://blogs.msdn.com/b/dawate/archive/2009/06/23/intro-to-audio-programming-part-2-demystifying-the-wav-format.aspx  # noqa
# ... for 16-bit WAV (sampwidth = 2), data range = -32760 to +32760

from __future__ import division
from __future__ import print_function
import math
import wave
import struct

DEBUG = True


def synthComplex(freq_coefs=[(440, 1)], duration_s=1.0, fname="test.wav",
                 frate_Hz=44100.00, amp_proportion=1.0):
    sine_list = []
    datasize = int(frate_Hz * duration_s)
    clipped = False
    for x in range(datasize):
        samp = 0
        for k in range(len(freq_coefs)):
            freq = freq_coefs[k][0]
            coef = freq_coefs[k][1]
            samp = samp + coef * math.sin(2 * math.pi * freq * (x / frate_Hz))
            # each component can contribute (+/- coef) to each sample
        if samp > 1 or samp < -1:
            clipped = True
        samp = min(max(samp, -1), 1)
        sine_list.append(samp)
    wav_file = wave.open(fname, "w")
    nchannels = 1
    sampwidth = 2
    maxamp = 32760  # as above
    framerate = int(frate_Hz)
    nframes = datasize
    comptype = "NONE"
    compname = "not compressed"
    wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype,
                        compname))
    ampfactor = amp_proportion * maxamp
    print("writing", fname)
    for s in sine_list:
        wav_file.writeframes(struct.pack('h', int(s * ampfactor)))
    wav_file.close()
    if clipped:
        print("warning: amplitude CLIPPED")


def frequencyHz(note, octave=4):
    badnote = "bad note"
    if (not note or not isinstance(note, str) or len(note) > 2
            or not isinstance(octave, int)):
        raise Exception(badnote)
    basenote = note[0].upper()
    notenum = 0  # will be: semitones relative to reference A (A4)
    if basenote == 'C':
        notenum = -9
    elif basenote == 'D':
        notenum = -7
    elif basenote == 'E':
        notenum = -5
    elif basenote == 'F':
        notenum = -4
    elif basenote == 'G':
        notenum = -2
    elif basenote == 'A':
        notenum = 0
    elif basenote == 'B':
        notenum = 2
    else:
        raise Exception(badnote)
    if len(note) == 2:
        modifier = note[1]
        if modifier == '#':  # sharp
            notenum += 1
        elif modifier == 'b':  # flat
            notenum -= 1
        else:
            raise Exception(badnote)
    notenum += 12 * (octave - 4)
    # Frequency = (twelfth root of 2) ^ note * 440 Hz
    # Frequency = 2 ^ (note / 12) * 440 Hz
    frequency_hz = pow(2, notenum / 12.0) * 440.0
    if DEBUG:
        print(note, octave, " = ", frequency_hz, " Hz")
    return frequency_hz
    # Test case: frequencyHz("A", 4) should return 440 (pitch standard)
    # Test case: frequencyHz("C", 4) should return 261.626 (middle C)
    # http://en.wikipedia.org/wiki/Scientific_pitch_notation


def ided3d():
    A4 = frequencyHz("A", 4)
    C4 = frequencyHz("C", 4)
    C5 = frequencyHz("C", 5)
    Eb5 = frequencyHz("Eb", 5)
    E5 = frequencyHz("E", 5)
    Fs5 = frequencyHz("F#", 5)
    G5 = frequencyHz("G", 5)
    C6 = frequencyHz("C", 6)

    synthComplex([(E5, 1/3), (G5, 1/3), (C6, 1/3)],
                 duration_s=0.164, fname="correct.wav")
    synthComplex([(A4, 1/4), (C5, 1/4), (Eb5, 1/4), (Fs5, 1/4)],
                 duration_s=0.550, fname="incorrect.wav")


if __name__ == '__main__':
    ided3d()
