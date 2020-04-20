#!/usr/bin/env python3
import os
import subprocess
import sys

from mpff import VALID_EXTENSIONS, get_file_extension
from tools import Prober, Uploader, log

ENCODING = 'utf8'
COPY_CODECS = ['aac', 'ac3', 'eac3']


def usage():
    log('Usage: ' + sys.argv[0] + ' <mkv_file>\n')


def get_cmd_params(old_file, new_file):
    prober = Prober(['-i', old_file])
    stream = prober.get_best_audio_stream()
    if stream is not None:
        bitrate = stream['bitrate'] if stream['bitrate'] is not None else '640k'
        if bitrate != '640k' and int(bitrate) > 640000:
            bitrate = '640k'
        lang = stream['language'] if stream['language'] is not None else 'eng'
        if stream['channels'] is not None:
            chan_no = int(stream['channels'])
            if chan_no > 6:
                chan_no = 6
            channels = ['-ac', str(chan_no)]
        else:
            channels = None
        cmd = ['-hwaccel', 'cuvid', '-i', old_file, '-map_chapters', '0', '-c:v', 'copy', '-map', '0:v:0']
        if stream['codec'] in COPY_CODECS:
            cmd += ['-c:a', 'copy', '-map', '0:a:' + str(stream['stream_no'])]
        else:
            cmd += ['-c:a', 'aac', '-aac_coder', 'twoloop', '-b:a',
                    str(bitrate)] + channels + ['-map', '0:a:' + str(stream['stream_no'])]
        if prober.has_text_subtitles():
            cmd += ['-c:s', 'copy', '-map', '0:s?']
        else:
            cmd += ['-sn']
        cmd += ['-metadata:s:a:' + str(stream['stream_no']), 'language=' + lang, new_file]
        log(' '.join(cmd))
        return cmd
    return None


def reencode(old_file, new_file):
    if os.getenv('DISPLAY') is None:
        ffmpeg = '/usr/bin/ffmpeg'
        has_window_manager = False
    else:
        ffmpeg = '/usr/bin/pff'
        has_window_manager = True
    cmd = [ffmpeg] + get_cmd_params(old_file, new_file)
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p_reencode:
        BUF_LEN = 4096
        read_fd = p_reencode.stdout.fileno() if has_window_manager else p_reencode.stderr.fileno()
        while True:
            buf = os.read(read_fd, BUF_LEN)
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
                new_file_path = orig_file_path[:-len(ext)-1] + '_2aac.mkv'
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
