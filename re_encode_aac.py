#!/usr/bin/env python3
import os
import subprocess
import sys
from threading import Lock, Thread

from tools import MediaContainer

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
    cmd = ['/usr/bin/ffmpeg', '-i', old_file]
    # cmd = ['cat', old_file]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p_bitrate:
        out, err = p_bitrate.communicate()
        container = None
        if err:
            container = MediaContainer(err)
        elif out:
            container = MediaContainer(out)
        if container:
            print(container.get_bitrate())
            print(container.get_streams())
            print(container.get_best_audio_source())
            print()
            br_data = container.get_bitrate()
            as_data = container.get_best_audio_source()
        if br_data is not None:
            cmd = ['/usr/bin/ffmpeg', '-hwaccel', 'cuvid', '-i', old_file, '-map_chapters', '0', '-c:v', 'copy', '-map', '0:v:0',
                   '-c:a', 'aac', '-vbr' '5', '-map', '0:a:' + str(as_data), new_file]
            log(' '.join(cmd))
            return
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
                except Exception:
                    raise
            else:
                log('not mkv file: ' + orig_file_path)


if __name__ == '__main__':
    main()
