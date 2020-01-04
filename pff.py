#!/usr/bin/env python3
import datetime
import os
import re
import subprocess
import sys

from tools import KDialogProgressBar, Prober

ENCODING = 'utf8'
BUF_LEN = 64
RE_BITRATE = re.compile('bitrate: \\d+ [a-zA-Z]')


def print_out(item):
    sys.stdout.write(item.decode(ENCODING))
    sys.stdout.flush()


def usage():
    print_out('Usage: ' + sys.argv[0] + ' <ffmpeg_args>\n')


def extract_time_str(time_bytes):
    # time_str example: frame=  399 fps=0.0 q=10.0 size=    1531kB time=00:00:16.57 bitrate= 756.5kbits/s speed=33.1x
    i = time_bytes.find(b'time=')
    if i >= 0:
        return time_bytes[i+5:i+13].decode(ENCODING)  # 00:00:16
    return None


def get_seconds(time_str):
    time_data = datetime.datetime.strptime(time_str, '%H:%M:%S')
    seconds = time_data.hour * 3600 + time_data.minute * 60 + time_data.second
    return seconds


def ffmpeg(args, progress_bar=None):
    cmd = ['/usr/bin/ffmpeg'] + args
    cmd = ['/usr/bin/script', '-qefc', ' '.join(cmd), '/dev/null']
    print(' '.join(cmd))
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
        line = b''
        while True:
            buf = os.read(p.stdout.fileno(), BUF_LEN)
            if buf == b'' and p.poll() is not None:
                break
            i = buf.find(b'\n')
            if i >= 0:
                line_with_buf = line + buf[:i+1]
                print_out(line_with_buf)
                if progress_bar:
                    time_str = extract_time_str(line_with_buf)
                    if time_str:
                        progress_bar.update(get_seconds(time_str))
                line = buf[i+1:]
            else:
                j = buf.find(b'\r')
                if j >= 0:
                    time_bytes = line + buf[:j+1]
                    print_out(time_bytes)
                    if progress_bar:
                        time_str = extract_time_str(time_bytes)
                        if time_str:
                            progress_bar.update(get_seconds(time_str))
                    line = buf[j+1:]
                else:
                    line += buf
        p.communicate()


def main():
    if len(sys.argv) < 2:
        usage()
    else:
        args = sys.argv[1:]
        prober = Prober(args)
        seconds = prober.get_duration()
        bar = KDialogProgressBar()
        bar.open(seconds, prober.file_name)
        try:
            ffmpeg(args, bar)
        finally:
            bar.close()


if __name__ == '__main__':
    main()
