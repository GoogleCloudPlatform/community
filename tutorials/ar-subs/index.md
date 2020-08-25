---
title: Create real-time translation overlays
description: Learn how to use the Media Translation API with streaming dialogue audio and create translated text overlays.
author: lepistom
tags: AI, artificial intelligence, ML, machine learning, IoT, Internet of Things, Raspberry Pi, video
date_published: 2020-08-26
---

Markku Lepisto | Solutions Architect | Google Cloud

This tutorial demonstrates the real-time speech-to-text transcribing and translation features of the
[Cloud Media Translation API](https://cloud.google.com/media-translation).

In this tutorial, you learn how to overlay translations as subtitles over a live video feed, using a video mixer and a luma keyer. The translated dialogue can be
projected onto surfaces as live subtitles using a projector, in effect creating [augmented reality (AR)](https://en.wikipedia.org/wiki/Augmented_reality) 
translations.

This tutorial uses the [pygame](https://www.pygame.org/wiki/about) library to control the HDMI output of a [Raspberry Pi](https://www.raspberrypi.org/)
computer. The HDMI output is then directed either to a projector or to a video mixer for luma key overlays. The overlay can then be used as live subtitles with, 
for example, video conference systems.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/arch-diag.svg)

## Objectives

- Create a Python client for the Media Translation API.
- Stream microphone or line-level audio to the service and receive real-time translations.
- Use pygame to output the translations through the Raspberry Pi HDMI port.
- Use a video mixer with a luma keyer to overlay translated subtitles on a video feed.
- Use a projector to display AR subtitles.

## Watch the companion video

To see this tutorial in action, you can watch the [Google Cloud Level Up episode](https://youtu.be/DvZRm-cqE7s). You can watch the video first, and then follow
the steps below yourself.

## Costs

This tutorial uses billable components of Google Cloud, including the Media Translation API.

This tutorial should not generate any usage that would not be covered by the
[free tier](https://cloud.google.com/free/), but you can use the
[pricing calculator](https://cloud.google.com/products/calculator/) to create
a cost estimate based on your projected production usage. For details, see
[Media Translation pricing and free tier](https://cloud.google.com/translate/media/pricing).

## Before you begin

This tutorial assumes that you already have a [Google Cloud account](https://console.cloud.google.com/freetrial).

Follow the instructions in the Media Translation documentation to
[set up your Google Cloud projects](https://cloud.google.com/translate/media/docs/streaming#set_up_your_project) to enable the Media Translation API.

## Required hardware

- Raspberry Pi (Model 3 B / B+ or 4 B recommended, but other models should also work.)
- Display device:
  - Small projector for displaying AR translations
  - Video mixer hardware or software, with luma keyer capabilities
  - Monitor to test this tutorial, instead of a projector
- Microphone to capture dialogue audio; either of the following:
  - USB microphone
  - USB sound card and an analog microphone or line level audio source
- USB keyboard for the Raspberry Pi
- 8 GB or larger microSD card for the Raspberry Pi operating system

## Raspberry Pi installation and configuration

###  Raspbian Lite OS installation and configuration

1.  Follow the [instructions to download the latest Raspbian Lite OS image](https://www.raspberrypi.org/documentation/installation/installing-images/README.md),
    and write it to your MicroSD card.

1.  Insert the MicroSD card into the Raspberry Pi card slot.

1.  Connect the USB keyboard to the Raspberry Pi.

1.  Connect the Raspberry Pi to a monitor or a projector using an HDMI cable.

1.  (Optional) If you use Ethernet connectivity, connect your ethernet cable to
    the Raspberry Pi.

1.  Connect the Raspberry Pi power supply to the wall socket and to the Raspberry Pi, which starts
    Raspbian OS.

1.  Log in to the Raspberry Pi with the initial username (`pi`) and password (`raspberry`).

1.  Start the Raspberry Pi configuration as the superuser:

        sudo raspi-config

1.  Select **1 Change User Password** to change the Raspberry Pi password.

1.  The recommended network connection method is an ethernet cable that
    provides a DHCP client IP to the Raspberry Pi. If you are using Wi-fi,
    select **2 Network Options** and then **N2 Wi-fi** to
    configure your Wi-fi country settings, SSID, and passphrase.

1.  Select **4 Localisation options** and then **I1 Change Locale**.

1.  Scroll down with the down arrow key, and deselect the default option
    (`en_GB.UTF-8 UTF-8`) using the space bar.

1.  Scroll down to `en_US.UTF-8 UTF-8` and select that option with the space
    bar.

1.  Press **Tabulator** and select **Ok**.

1.  Use the arrow keys in the **Configuring locales** window to select
    `en_US.UTF-8` from the list of choices as the default locale. Press
    **Tabulator** and select **Ok**.

1.  Select **4 Localisation options** and then **I2 Change Timezone**, and use
    the menu options to find your geographic region and country.
    
    Setting the timezone is important because some Google
    Cloud services require client devices' system clocks to be within 10
    minutes of real time. Raspbian uses global NTP time servers to synchronize
    the clock.

1.  (Optional) Select **4 Localisation options** and then **I3 Change Keyboard Layout**
    to match your layout.
    
    If you are not sure, select **Generic 105-key (Intl) PC**, **English (US)**,
    **The default for the keyboard layout**, and **No compose key**.

1.  Select **Interfacing Options**, **P2 SSH**, and then **Yes** to enable the
    SSH server on your Raspberry Pi.

1.  Select **Finish** to exit the `raspi-config` tool, and accept to restart the
    Raspberry Pi. If you are not prompted to reboot when you exit `raspi-config`, reboot the
    Raspberry Pi:

        sudo reboot

1.  Log in as the `pi` user with your new custom password.

1.  Verify that you have an IP address on your Raspberry Pi:

        ifconfig -a

    You should see a client IP address from your local network segment in either the
    `wlan0` or `eth0` interface.

1.  Verify that your DNS resolution and internet connection work:

        ping www.google.com

1.  If you do not have an IP address, or DNS resolution or internet connectivity
    fail, do not proceed further until you have fixed your Raspberry Pi's network
    configuration.
    
1.  If you are using Wi-Fi, check whether your Wi-Fi adapter has power saving
    enabled:

        iwconfig

    Power saving might give you sporadic network connectivity issues. Look for
    `Power Management` under the `wlan0` interface. If you see
    `Power Management:on`, then we recommend that you disable it for this tutorial.

    1.  On Raspberry Pi 3 model B/B+, disable `wlan0` Wi-Fi power management by configuring
        `/etc/network/interfaces`:

            sudo vi /etc/network/interfaces

        (This command uses `vi`. You can use `nano` if you prefer.)
    
        Add these lines to the end of the file:

            allow-hotplug wlan0
            iface wlan0 inet manual
                # disable wlan0 power saving
                post-up iw dev $IFACE set power_save off

    1.  Apply the changes by rebooting the Raspberry Pi:

            sudo reboot

    1.  Log in again as the `pi` user.

    1.  Ensure that Wi-fi power management is now off:

            iwconfig

        You should see `Power Management:off` for `wlan0`.

    1.  Check your internet connectivity:

            ping www.google.com

1.  Upgrade the Raspbian packages to latest versions:

        sudo apt-get update && sudo apt-get upgrade -y

### Install the Cloud SDK

1.  Log in to the Raspberry Pi with an SSH connection from your host computer:

        ssh pi@[YOUR_RASPBERRY_PI_IP_ADDRESS]
        
    With an SSH connection, you can copy and paste commands from this tutorial and linked pages to
    the Raspberry Pi.

1.  On the Raspberry Pi, follow all of the steps to [install and initialize the Cloud SDK for Debian systems](https://cloud.google.com/sdk/docs/#deb).
1.  Check that the Cloud SDK is installed and initialized:

        gcloud info

    Ensure that the `Account` and `Project` properties are set correctly.

### Install additional operating system packages

-   Install the required operating system packages:

        sudo apt-get update && sudo apt-get install -y git python3-dev python3-pygame python3-venv libatlas-base-dev libasound2-dev python3-pyaudio

### Increase console font size

This tutorial uses the HDMI console output of the Raspberry Pi as the main
display. If the default console font size is too small, you can use the
following steps to increase the font size and set it to Terminus 16x32.

1.  Start the `dpkg-reconfigure` utility:

        sudo dpkg-reconfigure console-setup

1.  Using the up and down arrow keys, select `UTF-8`. Using the right arrow key,
    select `OK`. Press Enter.

1.  Using the up and down arrow keys, select `Guess optimal character set`.
    Using the right arrow key, select `OK`. Press Enter.

1.  Using the up and down arrow keys, select `Terminus`. Using the right arrow key,
    select `OK`. Press Enter.

1.  Using the up and down arrow keys, select `16×32`. Using the right arrow key,
    select `OK`. Press Enter.

    The console is refreshed, and you are returned to the command prompt with the larger console font.

### Suppress some of the ALSA errors

On Raspberry Pi, the ALSA sound libraries may give errors when using
[PyAudio](https://pypi.org/project/PyAudio/) and the `pygame` library.

To suppress some of the ALSA errors when PyAudio starts, do the following:

1.  Back up the original ALSA configuration file:

        sudo cp /usr/share/alsa/alsa.conf /usr/share/alsa/alsa.conf.orig

1.  Edit the ALSA configuration file:
    1.  Search for the segment `#  PCM interface`.
    1.  Comment out the following lines with `#` as shown here:

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
dialogue. Raspberry Pi does not have analog microphone or line-level inputs.

There are several options to get spoken dialogue audio into the Raspberry Pi:

- USB microphone
- USB sound card with an analog microphone or any line-level audio feed connected to the sound card’s 3.5mm input
- Bluetooth microphone (This can be more complex to set up, and is out of scope for this tutorial.)

Connect and test a microphone with your Raspberry Pi:

1.  Connect the USB microphone to the Raspberry Pi or a USB soundcard to the
    Raspberry Pi, and an analog microphone to the sound card.

1.  List connected USB devices:

        lsusb
        
    The command should display something like the following example, which shows that the second line
    is the connected USB microphone:

        Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
        Bus 001 Device 005: ID 17a0:0310 Samson Technologies Corp. Meteor condenser microphone
        Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
        Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

1.  Identify the card and device numbers for the sound output options:

        aplay -l

    In this example, the Raspberry Pi built-in headphone output is card `0`, device `0`:

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

1.  Identify the sound input options:

        arecord -l
        
    In this example, the USB microphone is card `1`, device `0`:

        **** List of CAPTURE Hardware Devices ****
        card 1: Mic [Samson Meteor Mic], device 0: USB Audio [USB Audio]
          Subdevices: 1/1
          Subdevice #0: subdevice #0

1.  To configure the operating system to use the correct sound playback and microphone devices,
    edit or create the configuration file `/home/pi/.asoundrc`. (Note the dot in the
    file name `.asoundrc`. It is a so-called *hidden* configuration file.) Add
    the following content to the file and set the `mic` and `speaker` device
    numbers to be the same as your `aplay -l` and `arecord -l` output findings:

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

    In the preceding example, the microphone is set to `"hw:1,0"`, which means
    card 1 and device 0, which maps to the USB microphone. The speaker is
    set to card 0 and device 0, which maps to the Raspberry Pi built-in sound
    card's 3.5mm audio output.

### Test recording with the microphone

1.  Record a 5-second clip in 16KHz raw format:

        arecord --format=S16_LE --duration=5 --rate=16000 --file-type=raw out.raw

1.  Connect speakers or headphones to the configured sound output device, such as the Raspberry Pi 3.5mm audio output.

1.  Play the audio clip:

        aplay --format=S16_LE --rate=16000 out.raw

## Clone the example app and install its dependencies

1.  Using the SSH or console connection to the Raspberry Pi, clone the repository
    associated with the Google Cloud community tutorials:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Change to the tutorial directory:

        community/tutorials/ar-subs

1.  Create a Python 3 virtual environment:

        python3 -m venv venv

1.  Activate the virtual environment:

        source venv/bin/activate

1.  Upgrade `pip` and `setuptools`:

        pip3 install -U pip setuptools

1.  Install the required Python modules:

        pip3 install -r requirements.txt

### Create a service account and JSON key

In this section, you create a service account in your Google Cloud project and grant sufficient
permissions to it so that it can use the AI services. You also need download a JSON key for the service account. The JSON key will be used by the
Python utilities to authenticate with the Cloud services.

1.  Create a new service account:

        gcloud iam service-accounts create ml-dev --description="ML APIs developer access" --display-name="ML Developer Service Account"

1.  Grant the `ML Developer` role to the service account:

        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ml-dev@$PROJECT_ID.iam.gserviceaccount.com --role roles/ml.developer

1.  Grant the Project Viewer role to the service account:

        gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:ml-dev@$PROJECT_ID.iam.gserviceaccount.com --role roles/viewer

1. Create a JSON key for the service account:

        gcloud iam service-accounts keys create ./credentials.json --iam-account ml-dev@$PROJECT_ID.iam.gserviceaccount.com
        
     The key file is downloaded to the current working directory.


### Identify your USB microphone in python

In this section, you identify the USB microphone by its device number to make it visible to
Python. The device numbering for OS sound libraries may not match
the device numbering visible to Python apps, which is why you need to find
the microphone device again, this time with a Python utility.

1.  Within the Python virtual environment, execute the following command:

        python3 mic_identify.py

    The command should output something similar to the following, 
    which lists the example USB microphone in the first entry:

        (0, 'Samson Meteor Mic: USB Audio (hw:2,0)', 2)
        (1, 'dmix', 0)

1.  Record the device number. In the example above, it is `0`.


### Test recording with the USB microphone in Python

In this section, you record audio with the identified USB microphone device,
using PyAudio.

1.  The following command records a 3-second WAV audio file (mono, 16bits, 44.1KHz):

        python3 mic_test.py --dev 0
        
    This example uses the device `0` as identified with the previous command.

    The command should output something similar to the following:

        *** Recording 3 seconds with USB device 0 ***
        *** Finished recording. Wrote output: test1.wav ***

    You may get ALSA errors, but you can ignore them if the recording was
    successful.

1.  Listen to the test recording to make sure that it worked and that the dialogue
    sound quality is OK:

        aplay test1.wav

You may need to configure which interface the Raspberry Pi uses for sound playback
output. You can choose between the HDMI output and the 3.5mm line out / headphone jack,
by executing: `sudo raspi-config`, and configuring the setting
under
`7: Advanced Options → A4 Audio → Choose the audio output (HDMI | Headphones)`.

### Test the Media Translation API example Python client

Now that your USB microphone works with Python, you can call the Media
Translation API. This step tests calling the API in streaming mode, piping
microphone audio to the service, and displaying the translated live responses in
the command-line shell.

You can specify the [target language code](https://cloud.google.com/translate/media/docs/languages).
The default target language is `de-DE` for German.
    
To test with Italian, execute the following command, replacing the device number `0` with
your device number if necessary:

    python3 translate-microphone.py --lang it-IT --dev 0

Some of the target languages require a [Unicode](https://home.unicode.org/) font. By default,
the Raspberry Pi console font cannot display Unicode characters. For this
reason, use a Latin-based language such as German or Italian in this step, to
test the Media Translation API with your microphone. The next sections
show how to use the `ar-subs.py` app, which uses the `pygame` library and
specific fonts to display output in Hindi and Japanese.

### Test pygame with an HDMI display

In this section, you make sure that `pygame` can control the connected HDMI display or projector.

Test this by running an example game included in the `pygame` package:

1.  If you have been connected with SSH, you must now switch to the Raspberry Pi's HDMI
    output console—such as a monitor or a projector connected to the Raspberry Pi's HDMI
    port—and log in there.

1.  Change to the directory containing the example application:

        cd community/tutorials/ar-subs

1.  Activate the Python virtual environment:

        source venv/bin/activate

1.  Execute the `pygame` test game:

        python3 -m pygame.examples.aliens

1.  You should see a game on the console display:

    ![Pygame image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/aliens.png)

1.  You can control your car with the arrow keys and shoot with the space bar.

1.  The game will exit when you are hit.

1.  If you can see the game, `pygame` is working with your display and you can
    proceed to the next steps.

## Run the AR Subtitles application

In this section, you run the AR Subtitles application.

The app has two operating modes:

- Subtitles mode:
  - Subtitles are a luma effects video feed through the Raspberry Pi HDMI output,
    which can be overlaid on the primary video feed with a video mixer with a luma keyer.
  - Text is white, with a dark blue background behind the letters.
  - The rest of the screen is black, intended to be keyed out.
- Augmented Reality mode:
  - Translations are intended to be projected onto a surface in the real world using, for
    example, a pico projector.
  - Text is white, with a large font size to make it easily legible.
  - The rest of the screen black, which is not projected due to the pixel values being (0,0,0).

### Subtitles mode with a video mixer and luma keyer

**--position bottom**

In this mode, the Raspberry Pi's HDMI output must be connected to a video
mixer unit with luma keyer capabilities. The app displays a black
background, which is then keyed out. The luma keyer needs to be tuned so that it
keys out the background and leaves the translation output text as an overlay
on top of a video. With this mode, you can overlay translated subtitles on
any video feed, such as presentations and online video conference
applications.

To make the translated subtitles more legible on top of light-colored backgrounds
such as slides, the app adds a dark blue background behind the translated white
fonts. Otherwise white on white would not be seen. In this example, the app
adds a dark blue (RGB: 0,0,139) background behind the text, which can still be
visible after applying the luma keyer.

To make the translations work, connect the video source’s audio to the
Raspberry Pi’s audio input. This requires a USB sound card that has an audio
microphone or line-in connector. Then connect the Raspberry Pi HDMI output as a camera
source to the video mixer. With this setup, the video mixer has 2 video sources:

- the original video feed
- the Raspberry Pi translated subtitles output

Using the luma keyer in the mixer, key out the black background, and overlay
the remaining translated subtitles on the original video feed.

1.  View the command-line options:

        python3 ar-subs.py --help

1.  To start the app in subtitles mode, run the following, replacing the
    values with your desired options:

        python3 ar-subs.py --dev 0 --lang hi-IN --maxchars 85 --fontsize 46 --position bottom

    ![Sub0 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/sub0.png)

1.  After the app starts, you are presented with keys that you can press. The
    key presses are registered and handled by the `pygame` library. While the
    Media Translation API client is streaming an ongoing sentence, execution is
    blocked; key presses are acted on after the current sentence
    finishes. To finish a sentence, simply stop talking.

1.  To start translating, press any key. The screen will turn black. As you
    speak, the translations should start being displayed. You can enable
    or disable interim results by pressing the `i` key.

1.  To quit, press `q` and speak a bit more to register the key press.

    ![Sub1 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/sub1.png)

1.  Now that you have live translations displayed through the Raspberry Pi's HDMI port,
    you can use your video mixer's luma keyer to key out the black background.

    ![Sub2 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/sub2.png)

1.  The luma keyer settings are specific to each video mixer, but the general principle
    is the same: The keyer's input should be set to the Raspberry Pi HDMI
    output, and the keyer's luminance threshold should be set so that the black
    background is keyed out (removed), and the text with the blue background should
    remain as a transparent overlay. In this picture, you can see the Downstream
    Luma Keyer set to **On Air** with the example Blackmagic ATEM Mini Pro video mixer:

    ![Sub3 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/sub3.png)

1.  Now you can switch the mixer to the primary video feed, and have real-time
    translated subtitles. You can then use the video mixer output as a *webcam* and, for
    example, join a video conference with subtitles.

    ![Sub4 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/sub4.png)

### Augmented reality mode with a projector

**--position top**

In this mode, the translated text is intended to be projected onto real-world
physical surfaces, using a projector, in effect creating an augmented reality
display of the translation output. To make the text easily legible, this
mode uses very large font sizes.

**Note!** Projectors use very bright lamps that can be damaging to your eyes.
Never look directly into a projector lens, and never point the projector at a
person's head. If you test this solution with a projector, point it away from
people, at a surface, such as a wall.

1.  View the command-line options:

        python3 ar-subs.py --help

1.  To start the app in AR mode, run the following, replacing the
    values with your desired options:

        python3 ar-subs.py --dev 0 --lang de-DE -maxchars 42 --fontsize 120 --position top

1.  After the app starts, you are presented with keys that you can press. The
    key presses are registered and handled by the `pygame` library. While the
    Media Translation API client is streaming an ongoing sentence, execution is
    blocked; key presses are acted on after the current sentence
    finishes. To finish a sentence, simply stop talking.

1.  To start translating, press any key. The screen will turn black. As you
    speak, the translations should start being displayed. You can enable
    or disable interim results by pressing the `i` key.

1.  To quit, press `q` and speak a bit more to register the key press.

1.  After the app starts, point the projector at a surface where you want to
    display the subtitles.

1.  Experiment with different font sizes. Larger may be better, depending on
    where you project the text.

    ![Ar1 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/ar1.png)


### Test mode, translating lines in a text file

**--testfile**

The app has a testing mode, with the command line switch `--testmode`. In this
mode, the app reads the input text file and displays each line with the
configured font and display mode, line by line. You can use this mode to test
different font sizes and to simulate the app offline. In this mode, the app
displays each line in the file after a key press.

1.  Prepare an input text file. In order to display non-latin characters,
    you have to store the text in the file in Unicode format. A handy way is to use
    [Google Translate](https://translate.google.com) to create translated text in
    the target language, and then simply copy and paste the translated output into a
    text file.
    
    Assume you have the following line in a file `test.txt`:

        日本語テキストテスト

1.  Start the app in test mode:

        python3 ar-subs.py --lang ja-JP --maxchars 40 --fontsize --46 --position bottom --testfile test.txt

1.  After the app starts, press any key to display the next line in the input
    file. The app quits after it has displayed the last line, or if you press `q`.

    ![Test1 image](https://storage.googleapis.com/gcp-community/tutorials/ar-subs/test1.png)

### Example font sizes and line lengths

|      | Top: AR projector mode | Bottom: subtitles overlay mode |
|------|------------------------|--------------------------------|
| Latin languages (`--lang de-DE`) | `--maxchars 42 --fontsize 120 --position top` | `--maxchars 74 --fontsize 72 --position bottom` |
| Japanese (`--lang ja-JP`) | `--maxchars 20 --fontsize 92 --position top` | `--maxchars 40 --fontsize 46 --position bottom` |
| Hindi (`--lang hi-IN`) | `--maxchars 42 --fontsize 92 --position top` | `--maxchars 85 --fontsize 46 --position bottom` |


### Fonts used in the example

- Hindi: [Devanagari Noto Sans](https://fonts.google.com/specimen/Noto+Sans?subset=devanagari#about)
- Japanese: [Noto Sans JP](https://fonts.google.com/specimen/Noto+Sans+JP?query=noto+sans+jp&subset=japanese)

Fonts published by Google. Licensed under APACHE 2.0. Available at [fonts.google.com](http://fonts.google.com).

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete project**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

    ![deleting the project](https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png)

## What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
