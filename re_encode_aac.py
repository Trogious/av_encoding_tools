#!/usr/bin/env python3
import os
import subprocess
import sys
from threading import Lock, Thread

from mpff import VALID_EXTENSIONS, get_file_extension
from tools import Prober

ENCODING = 'utf8'

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


def reencode(old_file, new_file):
    prober = Prober(['-i', old_file])
    stream = prober.get_best_audio_stream()
    if stream is not None and stream['codec'] != 'aac':
        bitrate = stream['bitrate'] if stream['bitrate'] is not None else '640k'
        lang = stream['language'] if stream['language'] is not None else 'eng'
        # -metadata:s:v:0 language=eng
        cmd = ['/usr/bin/pff', '-hwaccel', 'cuvid', '-i', old_file, '-map_chapters', '0', '-c:v', 'copy', '-map', '0:v:0',
               '-c:a', 'aac', '-aac_coder', 'twoloop', '-b:a', str(bitrate), '-map', '0:a:' + str(stream['stream_no']),
               '-c:s', 'copy', '-map', '0:s?', '-metadata:s:a:' + str(stream['stream_no']), 'language=' + lang, new_file]
        log(' '.join(cmd))
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p_reencode:
            while True:
                buf = os.read(p_reencode.stdout.fileno(), 4096)
                if buf == b'' and p_reencode.poll() is not None:
                    break
                sys.stdout.write(buf.decode(ENCODING))
                sys.stdout.flush()
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
            ext = get_file_extension(orig_file_path)
            if ext in VALID_EXTENSIONS and os.path.isfile(orig_file_path):
                new_file_path = orig_file_path[:-len(ext)-1] + '_aac.mkv'
                try:
                    if os.path.exists(new_file_path):
                        log('output already exists: ' + new_file_path)
                    else:
                        reencode(orig_file_path, new_file_path)
                except Exception as e:
                    log(e)
                    raise
            else:
                log('not a supported file extension: ' + orig_file_path)


if __name__ == '__main__':
    main()
