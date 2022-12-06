#!/usr/bin/env python

from __future__ import print_function

import math
import os
import shlex
import subprocess
import pyAesCrypt
from time import time
from optparse import OptionParser

def get_video_length(filename):
    output = subprocess.check_output(("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                      "default=noprint_wrappers=1:nokey=1", filename)).strip()
    video_length = int(float(output))
    print("Video length in seconds: " + str(video_length))

    return video_length


def ceildiv(a, b):
    return int(math.ceil(a / float(b)))


def split_by_seconds(filename, split_length, vcodec="copy", acodec="copy",
                     extra="", video_length=None, **kwargs):
    if split_length and split_length <= 0:
        print("Split length can't be 0")
        raise SystemExit

    if not video_length:
        video_length = get_video_length(filename)
    split_count = ceildiv(video_length, split_length)
    if split_count == 1:
        print("Video length is less then the target split length.")
        raise SystemExit

    split_cmd = ["ffmpeg", "-i", filename, "-vcodec", vcodec, "-acodec", acodec] + shlex.split(extra)
    try:
        filebase = ".".join(filename.split(".")[:-1])
        fileext = filename.split(".")[-1]
    except IndexError as e:
        raise IndexError("No . in filename. Error: " + str(e))
    for n in range(0, split_count):
        split_args = []
        if n == 0:
            split_start = 0
        else:
            split_start = split_length * n

        split_args += ["-ss", str(split_start), "-t", str(split_length),
                       filebase + "-" + str(n + 1) + "-of-" +
                       str(split_count) + "." + fileext]
        print("About to run: " + " ".join(split_cmd + split_args))
        subprocess.check_output(split_cmd + split_args)


def main():
    parser = OptionParser()

    parser.add_option("-f", "--file",
                      dest="filename",
                      help="File to split, for example sample.avi",
                      type="string",
                      action="store"
                      )
    parser.add_option("-s", "--split-size",
                      dest="split_length",
                      help="Split or chunk size in seconds, for example 10",
                      type="int",
                      action="store"
                      )
    parser.add_option("-c", "--split-chunks",
                      dest="split_chunks",
                      help="Number of chunks to split to",
                      type="int",
                      action="store"
                      )
    parser.add_option("-S", "--split-filesize",
                      dest="split_filesize",
                      help="Split or chunk size in bytes (approximate)",
                      type="int",
                      action="store"
                      )
    parser.add_option("--filesize-factor",
                      dest="filesize_factor",
                      help="with --split-filesize, use this factor in time to"
                           " size heuristics [default: %default]",
                      type="float",
                      action="store",
                      default=0.95
                      )
    parser.add_option("--chunk-strategy",
                      dest="chunk_strategy",
                      help="with --split-filesize, allocate chunks according to"
                           " given strategy (eager or even)",
                      type="choice",
                      action="store",
                      choices=['eager', 'even'],
                      default='eager'
                      )
    parser.add_option("-m", "--manifest",
                      dest="manifest",
                      help="Split video based on a json manifest file. ",
                      type="string",
                      action="store"
                      )
    parser.add_option("-v", "--vcodec",
                      dest="vcodec",
                      help="Video codec to use. ",
                      type="string",
                      default="copy",
                      action="store"
                      )
    parser.add_option("-a", "--acodec",
                      dest="acodec",
                      help="Audio codec to use. ",
                      type="string",
                      default="copy",
                      action="store"
                      )
    parser.add_option("-e", "--extra",
                      dest="extra",
                      help="Extra options for ffmpeg, e.g. '-e -threads 8'. ",
                      type="string",
                      default="",
                      action="store"
                      )
    (options, args) = parser.parse_args()

    def bailout():
        parser.print_help()
        raise SystemExit

    if not options.filename:
        bailout()
    else:
        video_length = None
        if not options.split_length:
            video_length = get_video_length(options.filename)
            file_size = os.stat(options.filename).st_size
            split_filesize = None
            if options.split_filesize:
                split_filesize = int(options.split_filesize * options.filesize_factor)
            if split_filesize and options.chunk_strategy == 'even':
                options.split_chunks = ceildiv(file_size, split_filesize)
            if options.split_chunks:
                options.split_length = ceildiv(video_length, options.split_chunks)
            if not options.split_length and split_filesize:
                options.split_length = int(split_filesize / float(file_size) * video_length)
        if not options.split_length:
            bailout()
        split_by_seconds(video_length=video_length, **options.__dict__)
        encryptAes(options.__dict__["filename"], options.__dict__["split_chunks"])

def encryptAes(filename, split_chunks):
    # custom encryption/decryption buffer size (default is 64KB)
    bufferSize = 128 * 1024
    password = "please-use-a-long-and-random-password"
    print("###### ENCRYPTING AND DECRYPTING #######")
    # encrypt
    for x in range(split_chunks):
        start = time()
        pyAesCrypt.encryptFile(str(filename.split(".")[0]) + "-" + str(x+1) + "-of-"+ str(split_chunks)+ ".mp4", 
        str(filename.split(".")[0]) + "-"+ str(x+1) + "-of-" + str(split_chunks) + ".mp4.aes", password, bufferSize)
        end = time()
        print(end - start)
    
    # decrypt
    for x in range(split_chunks):
        start = time()
        pyAesCrypt.decryptFile(str(filename.split(".")[0]) + "-"+ str(x+1) + "-of-" + str(split_chunks) + ".mp4.aes",
        str(filename.split(".")[0]) + "-" + str(x+1) + "-of-"+ str(split_chunks)+ ".mp4", password, bufferSize)
        end = time()
        print(end - start)


if __name__ == '__main__':
    main()
