---
title: Creating Real-time Translation Overlays
description: Learn how to use the Media Translation API with streaming dialog audio, and create translated text overlays.
author: lepistom
tags: AI, Artificial Intelligence, ML, Machine Learning, IoT, Internet of Things, Raspberry Pi, Video
date_published: 2020-08-12
---

Markku Lepisto | Solutions Architect | Google Cloud Platform

This tutorial demonstrates the real-time speech-to-text transcribing and
translation functionality of the
[Cloud Media Translation API](https://cloud.google.com/media-translation).
The display method demonstrated is to overlay the translations as subtitles on
top of a live video feed, using a
[video mixer](https://en.wikipedia.org/wiki/Vision_mixer) and a
[luminance](https://en.wikipedia.org/wiki/Luma_(video)), or
[luma keyer](https://www.webopedia.com/TERM/L/luminance_keying.html).
Additionally, as a fun example, the translated dialog can be projected onto
surfaces as live subtitles, using a  projector. In effect,
creating [Augmented Reality](https://en.wikipedia.org/wiki/Augmented_reality)
(AR) translations.

The solution uses the [pygame](https://www.pygame.org/news) library to control
the HDMI output of a [Raspberry Pi](https://www.raspberrypi.org/) computer. The
HDMI output is then directed either to a projector, or a video mixer for luma
key overlays. The overlay can then be used as live subtitles with for example
video conference systems.

![architecture diagram][archdiag]

[archdiag]: img/arch-diag.svg


## Objectives

- Create a Python client for the Media Translation API.
- Stream microphone or line-level audio to the service and receive real-time
translations.
- Use pygame to output the translations via the Raspberry Pi HDMI port.
- Use a video mixer with a luma keyer, to overlay translated subtitles on top
of a video feed.
- Use a projector to display AR subtitles.


## Watch the companion video

If you wish to see this tutorial in action, you can watch the
[GCP Level Up episode](https://youtu.be/DvZRm-cqE7s) first, and then follow the
 steps below yourself.


## Before you begin

This tutorial assumes you already have a [Google Cloud Platform (GCP)](https://console.cloud.google.com/freetrial)
account set up.


## Costs

This tutorial uses billable components of GCP, including the following:

- Media Translation API

This tutorial should not generate any usage that would not be covered by the
[free tier](https://cloud.google.com/free/), but you can use the
[Pricing Calculator](https://cloud.google.com/products/calculator/) to generate
a cost estimate based on your projected production usage. Refer to
[Media Translation pricing and free tier](https://cloud.google.com/translate/media/pricing)
for more information.


## Enable the Media Translation API

[Set up your Google Cloud projects](https://cloud.google.com/translate/media/docs/streaming#set_up_your_project) to enable the Media Translation API.


## Required hardware

- Raspberry Pi. Models 3 B / B+ or 4 B recommended, but other models should
 work as well
- Display device
 - Small projector for displaying AR translations, or
 - Video mixer hardware or software, with luma keyer capabilities, or
 - Monitor to test this tutorial, instead of a projector
- Microphone to capture dialog audio, either
 - USB microphone or
 - USB sound card and an analog microphone or line level audio source
- USB keyboard for the Raspberry Pi
- 8GB or larger microSD card for the Raspberry Pi operating system (OS)


## Raspberry Pi installation and configuration

###  Raspbian Lite OS installation and configuration

1.  Follow the instructions [here][raspbian] to download the latest
    [Raspbian Lite OS image][raspbianimg], and write it on your MicroSD card.
1.  Insert the MicroSD card into the Pi card slot.
1.  Connect the USB keyboard into the Pi.
1.  Connect the Raspberry Pi to a monitor or a projector using a HDMI cable.
1.  Optionally, if you use Ethernet connectivity, connect your ethernet cable to
    the Pi.
1.  Connect the Pi power supply to the wall socket and to the Pi, to boot up
    Raspbian OS.
1.  Login to the Pi with the initial username: `pi` and password: `raspberry`
1.  Execute raspi-config as the superuser with:

        sudo raspi-config

1.  Change the pi user's password by selecting: **1 Change User Password**
1.  The recommended network connection method is an ethernet cable which
    provides a DHCP client IP to the Raspberry Pi. If you are using Wi-fi,
    select: **2 Network Options** then **N2 Wi-fi** to
    configure your Wi-fi country settings, SSID and passphrase.
1.  To get most console apps to display text correctly, select:
    **4 Localisation options** then **I1 Change Locale**. Scroll down with the
    down arrow key, and deselect the default option (`en_GB.UTF-8 UTF-8`) using
    the space bar.
1.  Scroll down to `en_US.UTF-8 UTF-8` and select that option with the space
    bar.
1.  Press Tabulator and select: **Ok**
1.  Use the arrow keys in the **Configuring locales** window to select
    `en_US.UTF-8` from the list of choices as the default locale. Press
    Tabulator and select: **Ok**
1.  To set your system timezone, select: **4 Localisation options** then
    **I2 Change Timezone** and use the menu options to find your geographic
    region and country. Setting the timezone is important because some Google
    Cloud services require client devices' system clocks to be within 10
    minutes of real time. Raspbian uses global NTP time servers to synchronize
    the clock.
1.  Optionally, select: **4 Localisation options** then
    **I3 Change Keyboard Layout** to match your layout. If you are not sure,
    select: **Generic 105-key (Intl) PC**, then **English (US)**, then **The
    default for the keyboard layout**, then **No compose key**.
1.  Select: **Interfacing Options**, then **P2 SSH**, then **Yes** to enable the
    SSH server on your Pi.
1.  Select: **Finish**, to exit the raspi-config tool and accept to restart the
    Pi. If you are not prompted to reboot when you exit raspi-config, reboot the
    Pi by executing:

        sudo reboot

1.  Log in as the `pi` user with your new custom password.
1.  Verify that you have an IP address on your Pi by executing:

        ifconfig -a

    You should see a client IP from your local network segment in either the
    `wlan0` or `eth0` interface.

1.  Verify that your DNS resolution and internet connection work, by executing:

        ping www.google.com

1.  If you do not have an IP address, or DNS resolution or internet connectivity
    fail, do not proceed further until you have fixed your Pi's network
    configuration.
1.  For Wi-fi connectivity only - check if your Wi-fi adapter has power saving
    enabled. You may wish to disable Wi-fi power saving, or it might give you sporadic
    network connectivity issues later on. Check the current state by executing:

        iwconfig

    Look for "Power Management" under the `wlan0` interface. If you see
    `Power Management:on`, then you have to disable it.

1.  On Pi 3 model B/B+, disable `wlan0` Wi-fi power management by configuring
    `/etc/network/interfaces`. Execute:

        sudo vi /etc/network/interfaces

    or use the nano editor if you prefer. Add these lines to the end of the file:

        allow-hotplug wlan0
        iface wlan0 inet manual
            # disable wlan0 power saving
            post-up iw dev $IFACE set power_save off

1.  Reboot the Pi with:

        sudo reboot

    to apply the changes. Then log in again as the `pi` user.

1.  Execute:

        iwconfig

    to ensure that Wi-fi power management is now: `Power Management:off` for
    `wlan0`.

1.  Execute:

        ping www.google.com

    to check your internet connectivity.

1.  Upgrade the Raspbian packages to latest versions with:

        sudo apt-get update && sudo apt-get upgrade -y

[raspbian]: https://www.raspberrypi.org/documentation/installation/installing-images/README.md
[raspbianimg]: https://www.raspberrypi.org/downloads/raspbian/


### Install Cloud SDK

1.  Login to the Pi with an SSH connection from your host computer. This way
you can easily copy & paste commands from this tutorial and linked pages, to
the Pi. Execute:

        ssh pi@<your-Pi-IP>

1.  On the Pi, follow all the steps [here][cloudsdk] to install and initialize
    Cloud SDK for Debian systems.
1.  Check that Cloud SDK is installed and initialized with:

        gcloud info

    Ensure that the `Account` and `Project` properties are set correctly.

[cloudsdk]: https://cloud.google.com/sdk/docs/#deb


### Install additional OS packages

1.  Execute the following command to install the required OS package dependencies:

        sudo apt-get update && sudo apt-get install -y git python3-dev python3-pygame python3-venv libatlas-base-dev libasound2-dev python3-pyaudio


### Increase console font size

This tutorial uses the HDMI console output of the Raspberry Pi as the main
display. If the default console font size is too small, you can execute the
following steps to increase the font size and set it to Terminus 16x32.

1. Execute the following command to run the `dpkg-reconfigure` utility:

        sudo dpkg-reconfigure console-setup

1. Using the up/down arrow keys select `UTF-8`. Then using the right arrow key
select `OK` and press ENTER.
1. Using the up/down arrow keys select `Guess optimal character set`. Then
using the right arrow key select “OK” and press ENTER.
1. Using the up/down arrow keys select `Terminus`. Using the right arrow key
select `OK` and press ENTER.
1. Using the up/down arrow keys select `16×32`. Using the right arrow key
select `OK` and press ENTER. The console will be refreshed and you will be
returned to the command prompt with the larger console font.


### Suppress some of the ALSA errors

On Raspberry Pi the ALSA sound libraries may output errors when using
[Pyaudio](https://pypi.org/project/PyAudio/) and the pygame library.
To suppress some of the ALSA errors when pyaudio starts, execute the following
steps:

1. Backup the original ALSA config file with:

        sudo cp /usr/share/alsa/alsa.conf /usr/share/alsa/alsa.conf.orig

2. Edit the ALSA config file:
    1. Search the segment `#  PCM interface`
    2. Comment out the following lines with: **#** as shown here:


          #pcm.front cards.pcm.front
          #pcm.rear cards.pcm.rear
          #pcm.center_lfe cards.pcm.center_lfe
          #pcm.side cards.pcm.side
          #pcm.surround21 cards.pcm.surround21
          #pcm.surround40 cards.pcm.surround40
          #pcm.surround41 cards.pcm.surround41
          #pcm.surround50 cards.pcm.surround50
          #pcm.surround51 cards.pcm.surround51
          #pcm.surround71 cards.pcm.surround71
          #pcm.iec958 cards.pcm.iec958
          #pcm.spdif iec958
          #pcm.hdmi cards.pcm.hdmi
          #pcm.modem cards.pcm.modem
          #pcm.phoneline cards.pcm.phoneline


### Connect and configure a microphone

The solution uses a microphone connected to the Raspberry Pi for recording the
dialog. Raspberry Pi does not have analog microphone or line level inputs.
There are several options to get spoken dialog audio into the Raspberry Pi:

- Using a USB microphone.
- Using a USB sound card with an analog microphone connected to the card’s 3.5mm input. Alternatively you can connect any line-level audio feed to the sound card.
- Using a Bluetooth microphone. This can be more complex to set up, and is out
of scope for this tutorial.

Execute the following steps to connect and test a microphone with your
Raspberry Pi:

1.  Connect the USB microphone to the Raspberry Pi or a USB soundcard to the
    Pi, and an analog microphone to the sound card.

1.  Execute `lsusb` to list connected USB devices. The command should display
something similar to the below example. The output shows that the second line
is the connected USB microphone:

        Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
        Bus 001 Device 005: ID 17a0:0310 Samson Technologies Corp. Meteor condenser microphone
        Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
        Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

1. To identify the card and device numbers for the **sound output** options, execute
`aplay -l`. In this example, the Raspberry Pi built-in headphone output is
card: `0`, device: `0`:

        card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
          Subdevices: 8/8
          Subdevice #0: subdevice #0
          Subdevice #1: subdevice #1
          Subdevice #2: subdevice #2
          Subdevice #3: subdevice #3
          Subdevice #4: subdevice #4
          Subdevice #5: subdevice #5
          Subdevice #6: subdevice #6
          Subdevice #7: subdevice #7
        card 1: Mic [Samson Meteor Mic], device 0: USB Audio [USB Audio]
          Subdevices: 1/1
          Subdevice #0: subdevice #0

1. To identify the **sound input** options, execute `arecord -l`. In this example
the USB microphone is card: `1`, device: `0`:

        **** List of CAPTURE Hardware Devices ****
        card 1: Mic [Samson Meteor Mic], device 0: USB Audio [USB Audio]
          Subdevices: 1/1
          Subdevice #0: subdevice #0

1. To configure the OS to use the correct sound playback and microphone devices,
edit or create the configuration file: `/home/pi/.asoundrc` (Note the dot in the
  file name `.asoundrc`. It is a so-called hidden configuration file.). Add
  the following content to the file and set the "mic" and "speaker" device
  numbers to be the same as your `aplay -l` and `arecord -l` output findings.
  In the following example, the microphone is set to "hw:1,0" which means
  card: 1 and device: 0 which maps to the USB microphone. And the "speaker" is
  set to card: 0 and device: 0 which maps to the Raspberry Pi built-in sound
  card's 3.5mm audio output.

        pcm.!default {
          type asym
          capture.pcm "mic"
          playback.pcm "speaker"
        }
        pcm.mic {
          type plug
          slave {
            pcm "hw:1,0"
          }
        }
        pcm.speaker {
          type plug
          slave {
            pcm "hw:0,0"
          }
        }


### Test recording with the microphone

1.  To test your microphone configuration, you can use the following command to
record a 5 second clip in 16KHz raw format:

        arecord --format=S16_LE --duration=5 --rate=16000 --file-type=raw out.raw

1.  To check the audio playback device and the recorded audio file, execute:

        aplay --format=S16_LE --rate=16000 out.raw

**Note:** you have to connect speakers or headphones to the configured sound
output device, such as the Raspberry Pi 3.5mm audio output.


## Clone the example app and install its dependencies

1.  Using the SSH or console connection to the Pi, clone the repository
associated with the Google Cloud community tutorials:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Change to the tutorial directory:

        community/tutorials/ar-subs

1.  Create a Python 3 virtual environment:

        python3 -m venv venv

1.  Activate the virtualenv:

        source venv/bin/activate

1.  Upgrade pip and setuptools:

        pip3 install -U pip setuptools

1.  Install the required Python modules:

        pip3 install -r requirements.txt


### Create a Service Account and JSON key

Next we will create a Service Account in your GCP project, and grant sufficient
permissions to it, so that it can use the AI services. You will also need to
download a JSON key for the Service Account. The JSON key will be used by the
Python utilities to authenticate with the Cloud services.

1. Create a new Service Account with the following command:

        gcloud iam service-accounts create ml-dev --description="ML APIs developer access" --display-name="ML Developer Service Account"

1. Grant the `ML Developer` role to the Service Account:

        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ml-dev@$PROJECT_ID.iam.gserviceaccount.com --role roles/ml.developer

1. Grant also the Project Viewer role to the Service Account:

        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ml-dev@$PROJECT_ID.iam.gserviceaccount.com --role roles/viewer

1. Create a JSON key for the Service Account. The key file will be downloaded to the current working directory:

        gcloud iam service-accounts keys create ./credentials.json --iam-account ml-dev@$PROJECT_ID.iam.gserviceaccount.com


### Identify your USB Microphone device number in python

Next we need to identify the device number of your USB microphone visible to
Python. Note that the device numbering for OS sound libraries may not match
the device numbering visible to Python apps. For this reason you need to find
the microphone device again, this time with a Python utility.

1. Within the python virtual environment, execute the following command:

        python3 mic_identify.py

The command should output something similar to this - with the example USB
microphone being the first entry listed here:


    (0, 'Samson Meteor Mic: USB Audio (hw:2,0)', 2)
    (1, 'dmix', 0)

2. Note down the device number - in the above example it is: `0`


### Test recording with the USB microphone in Python

Let’s try to record audio with the identified USB microphone device,
using `pyaudio`.

1. Execute the following command. The command should record a 3 second WAV
audio file (mono, 16bits, 44.1KHz). In this example we use the device `0` as
identified with the previous command:

        python3 mic_test.py --dev 0

The command should output something similar to:


    *** Recording 3 seconds with USB device 0 ***
    *** Finished recording. Wrote output: test1.wav ***

Note - you may get ALSA errors but you can ignore them, if the recording was
successful.

2. Listen to the test recording to make sure it worked and that the dialog
sound quality is ok. Execute:

        aplay test1.wav

You may need to configure which interface the Pi uses for sound playback
output. You can choose between the HDMI output and the 3.5mm line out /
headphone jack, by executing: `sudo raspi-config`, and configuring the setting
under `7: Advanced Options → A4 Audio → Choose the audio output (HDMI |
Headphones)`.


### Test the Media Translation API example Python client

Now that your USB microphone works with Python, you can try to call the Media
Translation API. This step will test calling the API in streaming mode, piping
microphone audio to the service and displaying the translated live responses in
 the command line shell.


1. Execute the utility with the following command. You can specify the [target language code](https://cloud.google.com/translate/media/docs/languages). The default target language is `de-DE` for German. For example to test with Italian, execute the below command.
In this example we use device number `0`. Replace that with your device number if
necessary:

        python3 translate-microphone.py --lang it-IT --dev 0

Note: some of the target languages require a
[Unicode](https://home.unicode.org/) font to be displayed correctly. By default
the Raspberry Pi console font cannot display Unicode characters. For this
reason, use a Latin-based language such as German or Italian in this step, to
test the Media Translation API with your microphone. The next chapters will
show how to use the `ar-subs.py` app which uses the pygame library and
specific fonts, to correctly display output in for example Hindi and Japanese.


### Test Pygame with an HDMI display

Now that the microphone is ready and the Media Translation API works,  make sure that pygame can control the connected HDMI display or projector. You can test this by running an example game included in the pygame package.

1. If you have been connected with SSH, you must now switch to the Pi's HDMI
output console. I.e a monitor or a projector connected to the Pi's HDMI port
and log in there.

1. Change to the solution app directory:

        cd community/tutorials/ar-subs

1. Activate the python virtual environment:

        source venv/bin/activate

1. Execute the pygame test game with:

        python3 -m pygame.examples.aliens

1. You should see a game on the console display:

![Pygame image][pygame]

[pygame]: img/aliens.png

6. You can control your car with the arrow keys and shoot with the space bar.
7. The game will exit when you are hit.
8. If you can see the game, pygame is working with your display and we can
proceed to the next steps.


## Execute the AR Subtitles application

Now you are ready to try the AR Subtitles application. The app has two operating
modes:

- Subtitles mode
  - in this mode, the subtitles are a luma effects video feed via the Raspberry
  Pi HDMI output. It can be overlaid on top of the primary video feed using a
  video mixer with a luma keyer
  - white text with a dark blue background behind the letters
  - rest of the screen black, intended to be keyed out
- Augmented Reality mode
  - in this mode, the translations are intended to be projected onto a surface
in the real world, using for example a pico projector
  - white text with a large font size to make it easily legible
  - rest of the screen black, which is not projected due to the pixel values
  being (0,0,0)


### Subtitles mode with a video mixer and luma keyer

**--position bottom**

In this mode, the Raspberry Pi's HDMI output has to be connected to a video
mixer unit which has luma keyer capabilities. The app displays a black
background which is then keyed out. The luma keyer needs to be tuned so that it
keys out the background and leaves the translation output text as an overlay
on top of a video. With this mode, you can add translated subtitles on top of
any video feed - including presentations and online video conference
applications.

To make the translated subtitles more legible, on top of e.g white background
such as slides, the app adds a dark blue background behind the translated white
fonts. Otherwise white-on-white would not be seen. In this example, the app
adds a dark blue (RGB: 0,0,139) background behind the text, which can still be
visible after applying the luma keyer.

To make the translations work, connect the video source’s audio to the
Raspberry Pi’s audio input. This requires a USB sound card that has an audio
mic or line-in connector. Then connect the Raspberry Pi HDMI output as a camera
source to the video mixer. Now the video mixer has 2 video sources:
- the original video feed, and
- the Raspberry Pi translated subtitles output

Using the luma keyer in the mixer, key out the black background, and overlay
the remaining translated subtitles on top of the original video feed.

1. See the command line options, by executing:

        python3 ar-subs.py --help

1. To start the app in subtitles mode, execute the following, replacing the
values with your desired options. Such as:

        python3 ar-subs.py --dev 0 --lang hi-IN --maxchars 85 --fontsize 46 --position bottom

  ![Sub0 image][sub0]

1. Once the app starts, you are presented with keys that you can press. The
key presses are registered and handled by the pygame library. But while the
Media Translation API client is streaming an ongoing sentence, the execution is
blocked. Thus the key presses will be acted on after the current sentence
finishes. To finish a sentence, simply stop talking.

1. To start translating, press any key. The screen will turn black and as you
speak, the translations should start being displayed. Note that you can enable
or disable interim results by pressing the key `i`.

1. To quit, press `q` and speak a bit more to register the key press.

  ![Sub1 image][sub1]

1. Now that you have live translations displayed through the Pi's HDMI port,
you can use your video mixer's luma keyer to key out the black background.

  ![Sub2 image][sub2]

1. The luma keyer settings are video mixer specific. But the general principle
is the same: the keyer's input should be set to the Raspberry Pi HDMI
output. And the keyer's luminance threshold should be set so that the black
background is keyed out (removed), and the text with the blue background should
remain as a transparent overlay. In this picture you can see the Downstream
Luma Keyer set to **On Air** with the example Blackmagic ATEM Mini Pro video mixer:

  ![Sub3 image][sub3]

1. Now you can switch the mixer to the primary video feed, and have real-time
translated subtitles. You can then use the video mixer output as a 'webcam' and
for example join a video conference with subtitles.

  ![Sub4 image][sub4]

[sub0]: img/sub0.png
[sub1]: img/sub1.png
[sub2]: img/sub2.png
[sub3]: img/sub3.png
[sub4]: img/sub4.png


### Augmented Reality mode with a projector

**--position top**

In this mode, the translated text is intended to be projected onto real world
physical surfaces, using a projector. In effect creating an Augmented Reality
display of the AI translation output. To make the text easily legible, this
mode uses very large font sizes.

**Note !** Projectors use very bright lamps that can be damaging to your eyes.
Never look directly into a projector lens, and never point the projector at a
person's head. If you test this solution with a projector, point it away from
people at surfaces such as a wall.

1. See the command line options, by executing:

        python3 ar-subs.py --help

1. To start the app in AR mode, execute the following, replacing the
values with your desired options. Such as:

        python3 ar-subs.py --dev 0 --lang de-DE -maxchars 42 --fontsize 120 --position top

1. Once the app starts, you are presented with keys that you can press. The
key presses are registered and handled by the pygame library. But while the
Media Translation API client is streaming an ongoing sentence, the execution is
blocked. Thus the key presses will be acted on after the current sentence
finishes. To finish a sentence, simply stop talking.

1. To start translating, press any key. The screen will turn black and as you
speak, the translations should start being displayed. Note that you can
enable or disable interim results by pressing the key `i`.

1. To quit, press `q` and speak a bit more to register the key press.

1. Once the solution starts, point the projector at a surface where you want to
display the subtitles.

1. Experiment with different font sizes. Larger may be better, depending on
where you project the text.

    ![Ar1 image][ar1]

  [ar1]: img/ar1.png


### Test mode, translating lines in a text file

**--testfile**

The app has a testing mode, with the command line switch --testmode. In this
mode, the app reads the input text file and displays each line with the
configured font and display mode, line by line. You can use this mode to test
different font sizes and to simulate the app offline. In this mode, the app
displays each line in the file after a key press.

1. Prepare an input text file. Note - in order to display non-latin languages,
you have to store the text in the file in Unicode format. A handy way is to use
[Google Translate](https://translate.google.com) to create translated text in
the target language, and then simply copy & paste the Translation output into a
text file. Here let's assume you have the following line in a file `test.txt`:

        日本語テキストテスト

1. To start the app in test mode, execute for example:

        python3 ar-subs.py --lang ja-JP --maxchars 40 --fontsize --46 --position bottom --testfile test.txt

1. After the app starts, press any key to display the next line in the input
file. The app quits after it has displayed the last line, or if you press `q`.

  ![Test1 image][test1]

[test1]: img/test1.png


### Example font sizes and line lengths


<table>
  <tr>
   <td>
   </td>
   <td><strong>Top - AR projector mode</strong>
   </td>
   <td><strong>Bottom - subtitles overlay mode</strong>
   </td>
  </tr>
  <tr>
   <td>Generic latin languages --lang de-DE | it-IT
   </td>
   <td>--maxchars 42 --fontsize 120 --position top
   </td>
   <td>--maxchars 74 --fontsize 72 --position bottom
   </td>
  </tr>
  <tr>
   <td>Japanese --lang ja-JP
   </td>
   <td>--maxchars 20 --fontsize 92 --position top
   </td>
   <td>--maxchars 40 --fontsize 46 --position bottom
   </td>
  </tr>
  <tr>
   <td>Hindi --lang hi-IN
   </td>
   <td>--maxchars 42 --fontsize 92 --position top
   </td>
   <td>--maxchars 85 --fontsize 46 --position bottom
   </td>
  </tr>
</table>


### Fonts used in the example

- Hindi: [Devanagari Noto Sans](https://fonts.google.com/specimen/Noto+Sans?subset=devanagari#about)
- Japanese: [Noto Sans JP](https://fonts.google.com/specimen/Noto+Sans+JP?query=noto+sans+jp&subset=japanese)

Fonts published by Google. Licensed under APACHE 2.0. Available at [fonts.google.com](http://fonts.google.com).


## Cleaning up

### Delete the GCP project

To avoid incurring charges to your GCP account for the resources used in this tutorial, you can delete the project.

**Caution**: Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
an `appspot.com` URL, remain available.

To delete a project, do the following:

1. In the GCP Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

[delete-project]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png
![deleting the project][delete-project]

## What's next

- Watch this tutorial's [GCP Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o)
- Learn more about [AI on GCP](https://cloud.google.com/solutions/ai/)
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools)
- Try out other GCP features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
