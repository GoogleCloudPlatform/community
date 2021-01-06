# -*- coding: utf-8 -*-

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pyaudio
import wave
import argparse


def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--dev',
            default=0,
            type=int,
            help='USB Microphone device number to use. Default: 0')
    return parser.parse_args()


args = parse_command_line_args()
form_1 = pyaudio.paInt16  # 16-bit resolution
chans = 1  # 1 channel
samp_rate = 44100  # 44.1kHz sampling rate
chunk = 4096  # 2^12 samples for buffer
record_secs = 3  # seconds to record
dev_index = args.dev  # device index found by p.get_device_info_by_index(ii)
wav_output_filename = 'test1.wav'  # name of .wav file

audio = pyaudio.PyAudio()  # create pyaudio instantiation

# create pyaudio stream
stream = audio.open(format=form_1, rate=samp_rate, channels=chans,
                    input_device_index=dev_index, input=True,
                    frames_per_buffer=chunk)
print("\n*** Recording 3 seconds with USB device {} ***\n".format(args.dev))
frames = []

# loop through stream and append audio chunks to frame array
for ii in range(0, int((samp_rate/chunk)*record_secs)):
    data = stream.read(chunk)
    frames.append(data)

print("*** Finished recording. Wrote output: {} ***\n".format(wav_output_filename))

# stop the stream, close it, and terminate the pyaudio instantiation
stream.stop_stream()
stream.close()
audio.terminate()

# save the audio frames as .wav file
wavefile = wave.open(wav_output_filename, 'wb')
wavefile.setnchannels(chans)
wavefile.setsampwidth(audio.get_sample_size(form_1))
wavefile.setframerate(samp_rate)
wavefile.writeframes(b''.join(frames))
wavefile.close()
