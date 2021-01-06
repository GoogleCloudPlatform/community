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
from __future__ import division

import os
import itertools
import pygame
import pyaudio
import argparse
from six.moves import queue
from google.cloud import mediatranslation as media


# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
SpeechEventType = media.StreamingTranslateSpeechResponse.SpeechEventType
log_file = 'ar-subs.log'


def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=(
            'Media Translation live subtitles demo.'))
    parser.add_argument(
            '--dev',
            default=0,
            type=int,
            help='USB Microphone device number to use.')
    parser.add_argument(
            '--lang',
            default="de-DE",
            type=str,
            help='Translation target language code. Default: de-DE')
    parser.add_argument(
            '--credentials',
            default="./credentials.json",
            type=str,
            help='Service account JSON key. Default: ./credentials.json')
    parser.add_argument(
            '--fontsize',
            default=100,
            type=int,
            help='Font size in pixels.')
    parser.add_argument(
            '--maxchars',
            default=40,
            type=int,
            help='Max characters per line.')
    parser.add_argument(
            '--position',
            default='bottom',
            choices=['top', 'bottom'],
            help='Display on the top if set. Default is on the bottom.')
    parser.add_argument(
            '--testfile',
            type=str,
            help='Test mode. Does not use API, displays each row in testfile after key presses.')
    return parser.parse_args()


class pyprojector:
    screen = None
    x = None
    y = None

    def __init__(self, log):
        "Initializes a new pygame screen using the framebuffer"
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            log.write("I'm running under X display = {0}".format(disp_no))
            log.flush()

        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                log.write('Driver: {0} failed.'.format(driver))
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        self.x = pygame.display.Info().current_w
        self.y = pygame.display.Info().current_h
        log.write("Framebuffer resolution: %d x %d\n" % (self.x, self.y))
        log.flush()
        self.screen = pygame.display.set_mode((self.x, self.y),
                                              pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def clear(self):
        # clear the screen
        self.screen.fill((0, 0, 0))
        pygame.display.update()

    def drawGraticule(self):
        # Active area = 0,0 to self.x,self.y pixels
        color = (255, 255, 255)
        pygame.draw.rect(self.screen, color, (0, 0, self.x - 1, self.y - 1), 1)
        pygame.display.update()

    def show_text(self, text, font, fontsize, position):
        self.screen.fill((0, 0, 0))
        text_surface = font.render(text, True, (255, 255, 255))
        if position == 'top':
            self.screen.blit(text_surface, (0, 0))
        else:
            y = self.y - text.surface.get_height()
            self.screen.blit(text_surface, (0, y))
        pygame.display.update()

    def show_text_multi_line(self, text_multi, font, fontsize, position):
        self.screen.fill((0, 0, 0))

        for i in range(len(text_multi)):
            text = text_multi[i]
            text_surface = font.render(text, True, (255, 255, 255))
            h = text_surface.get_height()
            if position == 'bottom':
                offset = self.y - (h * len(text_multi)) - 150
                y = i * h + offset
                temp_surface = pygame.Surface(text_surface.get_size())
                temp_surface.fill((0, 0, 139))
                temp_surface.blit(text_surface, (0, 0))
                self.screen.blit(temp_surface, (0, y))
            else:
                offset = 0
                y = i * h + offset
                self.screen.blit(text_surface, (0, y))
        pygame.display.update()

    def get_size(self):
        return (self.x, self.y)


class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk, dev_index):
        self._rate = rate
        self._chunk = chunk
        self._dev_index = dev_index

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            input_device_index=self._dev_index,
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type=None, value=None, traceback=None):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def exit(self):
        self.__exit__()

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def split_words(translation, maxchars, log, lang):
    tr = []

    if len(translation) <= maxchars:
        return [translation]
    else:
        if lang == 'th-TH' or lang == 'ja-JP':
            # Words not separated by space
            line = ""
            for letter in translation:
                line = line + letter
                if len(line) >= maxchars:
                    tr.append(line)
                    line = ""
            if len(line) > 0:
                tr.append(line)
        else:
            # Words are separated by space
            tr_temp = translation.split(' ')
            line = ""
            rng = len(tr_temp)
            for i in range(rng):
                t = tr_temp[i]
                if len(line) + len(t) <= maxchars:
                    if i == 0:
                        line = t
                    else:
                        # continue same line
                        line = line + ' ' + t
                else:
                    # switch to next line
                    tr.append(line)
                    line = t
                if i == rng - 1:
                    # add last line to the list
                    tr.append(line)
    log.write("Split_words: [{}] to: [{}]\n".format(translation, tr))
    log.flush()
    return tr


def listen_print_loop(responses, args, projector, font, fontsize, log, interim):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.
    """
    translation = ''
    maxchars = args.maxchars
    position = args.position
    tr = ''

    for response in responses:
        # Once the transcription settles, the response contains the
        # END_OF_SINGLE_UTTERANCE event.
        if (response.speech_event_type ==
                SpeechEventType.END_OF_SINGLE_UTTERANCE):
            log.write("Final!\n")
            log.flush()
            projector.show_text_multi_line(tr, font, fontsize, position)
            return 0

        result = response.result
        translation = result.text_translation_result.translation
        log.write("Got result: [{}]\n".format(translation))
        log.flush()
        tr = split_words(translation, maxchars, log, args.lang)

        if interim:
            projector.show_text_multi_line(tr, font, fontsize, position)


def do_translation_loop(args, projector, font, fontsize, log, interim):
    dev_index = args.dev
    lang = args.lang

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            log.write("-- CLEAN EXIT ---\n")
            log.close()
            exit(0)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            log.write("c pressed - clear screen\n")
            log.flush()
            projector.clear()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            interim = not interim
            log.write("i pressed. Interim results: {}\n".format(interim))
            log.flush()
        else:
            continue

    client = media.SpeechTranslationServiceClient()

    speech_config = media.TranslateSpeechConfig(
        audio_encoding='linear16',
        source_language_code='en-US',
        target_language_code=lang)

    config = media.StreamingTranslateSpeechConfig(
        audio_config=speech_config, single_utterance=True)

    # The first request contains the configuration.
    # Note that audio_content is explicitly set to None.
    first_request = media.StreamingTranslateSpeechRequest(
        streaming_config=config, audio_content=None)

    with MicrophoneStream(RATE, CHUNK, dev_index) as stream:
        audio_generator = stream.generator()
        mic_requests = (media.StreamingTranslateSpeechRequest(
            audio_content=content,
            streaming_config=config)
            for content in audio_generator)

        requests = itertools.chain(iter([first_request]), mic_requests)

        responses = client.streaming_translate_speech(requests)

        # Print the translation responses as they arrive
        result = listen_print_loop(responses, args, projector, font, fontsize, log, interim)
        if result == 0:
            stream.exit()
    return interim


def test_display(args, log, font, fontsize, projector):
    # Display the test text following the other parameters
    # Exit after any key pressed
    maxchars = args.maxchars
    position = args.position

    tf = open(args.testfile, 'r')
    for line in tf:
        tr = ''
        tr = split_words(line, maxchars, log, args.lang)
        projector.show_text_multi_line(tr, font, fontsize, position)

        pygame.event.clear()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    log.write("-- CLEAN EXIT ---\n")
                    log.close()
                    exit(0)
                else:
                    break
    tf.close()
    log.write("-- CLEAN EXIT ---\n")
    log.close()
    exit(0)
    return


def main():
    # Main start
    log = open(log_file, 'a')
    log.write('--- START ---\n')
    args = parse_command_line_args()
    lang = args.lang
    fontsize = args.fontsize
    interim = False
    position = args.position
    log.write('Display position: {}, '.format(position))

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials

    # pygame init for direct framebuffer drawing for laser projector
    pygame.init()
    pygame.mouse.set_visible(0)

    if lang == 'hi-IN':
        log.write('Hindi\n')
        font = pygame.font.Font('fonts/NotoSans-Bold.ttf', fontsize)
    elif lang == 'ja-JP':
        log.write('Japanese\n')
        font = pygame.font.Font('fonts/NotoSansJP-Bold.otf', fontsize)
    else:
        log.write('Latin languages\n')
        font = pygame.font.Font(None, fontsize)
    log.flush()

    # Create an instance of the PyGame PyProjector class
    projector = pyprojector(log)

    # Test mode - skip the rest and just display the set text
    if args.testfile:
        test_display(args, log, font, fontsize, projector)

    # Display a quick help screen and projection area grid
    projector.drawGraticule()
    projector.show_text_multi_line(["Press any key to start translating", " ",
                                    "Press q to quit", "Press c to clear the screen",
                                    "Press i to enable or disable interim results",
                                    " ", "To register the key presses, speak a sentence"],
                                   pygame.font.Font(None, 72), 72, 'top')
    projector.drawGraticule()
    pygame.event.clear()
    while True:
        event = pygame.event.wait()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                log.write("-- CLEAN EXIT ---\n")
                log.close()
                exit(0)
            elif event.key == pygame.K_i:
                interim = not interim
                log.write("i pressed. Interim results: {}\n".format(interim))
                log.flush()
            else:
                break
    projector.clear()

    while True:
        interim = do_translation_loop(args, projector, font, fontsize, log, interim)


if __name__ == "__main__":
    main()
