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


def write_txt(subs, args):
    txt_file = args.srt + ".txt"
    f = open(txt_file, 'w')
    for sub in subs:
        f.write(sub.content.replace("\n", " ") + '\n')
    f.close()
    print("Wrote text file {}".format(txt_file))
    return


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--srt",
        type=str,
        default="en.srt",
    )
    args = parser.parse_args()

    subs = load_srt(args.srt)
    write_txt(subs, args)


if __name__ == "__main__":
    main()
