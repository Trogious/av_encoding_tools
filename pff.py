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


def extract_time_str(time_str):
    # time_str example: frame=  399 fps=0.0 q=10.0 size=    1531kB time=00:00:16.57 bitrate= 756.5kbits/s speed=33.1x
    i = time_str.find(b'time=')
    if i >= 0:
        return time_str[i+5:i+13].decode(ENCODING)  # 00:00:16
    return time_str


def get_seconds(time_str):
    time_data = datetime.datetime.strptime(time_str, '%H:%M:%S')
    seconds = time_data.hour * 3600 + time_data.minute * 60 + time_data.second
    return seconds


def ffmpeg(args, progress_bar=None):
    cmd = ['/usr/bin/ffmpeg'] + args
    cmd = ['/usr/bin/script', '-qefc', ' '.join(cmd), '/dev/null']
    print(' '.join(cmd))
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        line = b''
        while True:
            buf = os.read(p.stdout.fileno(), BUF_LEN)
            if buf == b'' and p.poll() is not None:
                break
            i = buf.find(b'\n')
            if i >= 0:
                print_out(line + buf[:i+1])
                line = buf[i+1:]
            else:
                j = buf.find(b'\r')
                if j >= 0:
                    time_str = line + buf[:j]
                    seconds = get_seconds(extract_time_str(time_str))
                    print_out(b'\r' + time_str)
                    if progress_bar:
                        progress_bar.update(seconds)
                    line = buf[j+1:]
                else:
                    line += buf
        p.communicate()


def main():
    subprocess.run(['/sbin/modprobe', 'nvidia_uvm'])
    print_out(b"\x1b[1;%dm" % (31) + b"colors test" + b"\x1b[0m")
    print()
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
