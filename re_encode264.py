#!/usr/bin/env python3
import os
import re
import subprocess
import sys

from mpff import VALID_EXTENSIONS, get_file_extension
from tools import Uploader, log

ENCODING = 'utf8'
FFMPEG = '/usr/bin/ffmpeg' if os.getenv('DISPLAY') is None else '/usr/bin/pff'
RE_BITRATE = re.compile('bitrate: \\d+ [a-zA-Z]')


def usage():
    log('Usage: ' + sys.argv[0] + ' <mkv_file>\n')


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
            cmd = [FFMPEG, '-hwaccel', 'cuvid', '-i', old_file, '-c:v', 'h264_nvenc', '-preset', 'slow', '-rc', 'vbr_hq',
                   '-b:v', br_data[0], '-pix_fmt', 'yuv420p', '-maxrate:v', br_data[0], '-map', '0:v:0', '-c:a', 'copy', '-map', '0:a',
                   # '-c:s', 'copy', '-map', '0:s', '-map_chapters', '0', new_file]
                   '-sn', '-map_chapters', '0', new_file]
            cmd = ['/usr/bin/pff', '-hwaccel', 'cuvid', '-i', old_file, '-c:v', 'copy',
                   '-map', '0:v:0', '-c:a', 'copy', '-map', '0:a',
                   # '-c:s', 'copy', '-map', '0:s', '-map_chapters', '0', new_file]
                   '-sn', '-map_chapters', '0', new_file]
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
                    Uploader(new_file).run()
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
                if orig_file_path[:-len(ext)-1].endswith('_mpeg2'):
                    new_file_path = orig_file_path.replace('_mpeg2', '_h264')
                else:
                    new_file_path = orig_file_path.replace('.mkv', '_h264.mkv').replace('.mp4', '_h264.mkv')
                try:
                    if os.path.exists(new_file_path):
                        log('output already exists: ' + new_file_path)
                    else:
                        reencode(orig_file_path, new_file_path)
                except Exception as e:
                    log(e)
            else:
                log('not a supported file extension: ' + orig_file_path)


if __name__ == '__main__':
    main()
