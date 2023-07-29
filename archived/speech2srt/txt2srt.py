# -*- coding: utf-8 -*-
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import srt


def load_srt(filename):
    # load original .srt file
    # parse .srt file to list of subtitles
    print("Loading {}".format(filename))
    with open(filename) as f:
        text = f.read()
    return list(srt.parse(text))


def process_translations(subs, indexfile):
    # read index.csv and foreach translated file,

    print("Updating subtitles for each translated language")
    with open(indexfile) as f:
        lines = f.readlines()
    # copy orig subs list and replace content for each line
    for line in lines:
        index_list = line.split(",")
        lang = index_list[1]
        langfile = index_list[2].split("/")[-1]
        lang_subs = update_srt(lang, langfile, subs)
        write_srt(lang, lang_subs)
    return


def update_srt(lang, langfile, subs):
    # change subtitles' content to translated lines

    with open(langfile) as f:
        lines = f.readlines()
    i = 0
    for line in lines:
        subs[i].content = line
        i += 1
    return subs


def write_srt(lang, lang_subs):
    filename = lang + ".srt"
    f = open(filename, "w")
    f.write(srt.compose(lang_subs, strict=True))
    f.close()
    print("Wrote SRT file {}".format(filename))
    return


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--srt",
        type=str,
        default="en.srt",
    )
    parser.add_argument(
        "--index",
        type=str,
        default="index.csv",
    )
    args = parser.parse_args()

    subs = load_srt(args.srt)
    process_translations(subs, args.index)


if __name__ == "__main__":
    main()
