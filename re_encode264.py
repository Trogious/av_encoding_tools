#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from threading import Lock, Thread

ENCODING = 'utf-8'
RE_BITRATE = re.compile('bitrate: \\d+ [a-zA-Z]')

YUP_stderr_lock = Lock()
YUP_stderr = sys.stderr


def log(log_item):
    with YUP_stderr_lock:
        YUP_stderr.write(str(log_item) + '\n')
        YUP_stderr.flush()


def usage():
    log('Usage: ' + sys.argv[0] + ' <mkv_file>\n')


class Uploader(Thread):
    def __init__(self, file):
        Thread.__init__(self)
        self.file = file

    def run(self):
        cmd = ['/home/dupa/tv/s_r2d2.sh', self.file]
        try:
            subprocess.run(cmd)
        except Exception as e:
            log(e)


def get_bitrate(output):
    out = output.decode(ENCODING)
    for line in out.splitlines():
        if 'bitrate' in line:
            m = RE_BITRATE.search(line)
            if m is not None:
                g = m.group()
                bitrate = int(g.replace('bitrate: ', '')[:-2])
                unit = g[-1].lower()
                if unit == 'k':
                    max_bitrate = str(int(bitrate / 1000) + 1) + 'M'
                else:
                    max_bitrate = '10M'
                return (str(bitrate) + unit, max_bitrate)
    return (0, 'b')


def reencode(old_file, new_file):
    cmd = ['/usr/bin/ffmpeg', '-i', old_file]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p_bitrate:
        out, err = p_bitrate.communicate()
        br_data = None
        if err is not None:
            br_data = get_bitrate(err)
        elif out is not None:
            br_data = get_bitrate(out)
        if br_data is not None:
            cmd = ['/usr/bin/ffmpeg', '-hwaccel', 'cuvid', '-i', old_file, '-c:v', 'h264_nvenc', '-preset', 'slow',
                   '-b:v', br_data[0], '-maxrate:v', br_data[1], '-pix_fmt', 'yuv420p', '-c:a', 'copy', new_file]
            log(' '.join(cmd))
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p_reencode:
                p_reencode.communicate()
                if p_reencode.returncode == 0:
                    log('re-encoding done')
#                    Uploader(new_file).run()
                else:
                    log('re-encoding failed')


def main():
    a_len = len(sys.argv)
    if a_len < 2:
        usage()
    else:
        subprocess.run(['/sbin/modprobe', 'nvidia_uvm'])
        for orig_file_path in sys.argv[1:]:
            if (orig_file_path.endswith('.mkv') or orig_file_path.endswith('.mp4')) and os.path.isfile(orig_file_path):
                try:
                    new_file_path = orig_file_path.replace('.mkv', '_2.mkv').replace('.mp4', '_2.mkv')
                    if os.path.exists(new_file_path):
                        log('output already exists: ' + new_file_path)
                    else:
                        reencode(orig_file_path, new_file_path)
                except Exception as e:
                    log(e)
            else:
                log('not mkv file: ' + orig_file_path)


if __name__ == '__main__':
    main()
