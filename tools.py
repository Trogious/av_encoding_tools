import json
import os
import re
import subprocess

import dbus

ENCODING = 'utf8'
PROGRESS_DIALOG = 'org.kde.kdialog.ProgressDialog'
DBUS_PROPS = 'org.freedesktop.DBus.Properties'
RE_BITRATE = re.compile('bitrate: \\d+ [a-zA-Z]')
# Stream #0:0(eng): Video: h264
RE_STREAM = re.compile('Stream #\\d:\\d\\([a-z][a-z][a-z]\\): [a-zA-Z0-9_]+: [a-zA-Z0-9_]+')
RE_AUDIO_CODECS_PRIORITY = ['truehd', 'dts', 'aac', 'eac3', 'ac3', 'mp3']
PFF_BUS_NAME = os.getenv('PFF_BUS_NAME')
PFF_OBJECT_PATH = os.getenv('PFF_OBJECT_PATH')


def jl(obj):
    log_str = json.dumps(obj, sort_keys=True, indent=2, separators=(',', ': '))
    print(log_str)


class MediaContainer:
    def __init__(self, ffmpeg_i_output):
        self.output = ffmpeg_i_output.decode(ENCODING)

    def get_bitrate(self):
        out = self.output
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

    def get_audio_streams(self):
        streams = []
        for line in self.output.splitlines():
            if 'Stream' in line:
                m = RE_STREAM.search(line)
                if m is not None:
                    g = m.group()
                    media = {}
                    parts = g.split(':')[1:]
                    stream_lang = parts[0].split('(')
                    media['stream_no'] = stream_lang[0].strip()
                    media['language'] = stream_lang[1][:-1].strip().lower()
                    media['type'] = parts[1].strip().lower()
                    media['codec'] = parts[2].strip().lower()
                    streams.append(media)
        return streams

    def get_best_audio_stream(self):
        streams = self.get_audio_streams()
        filtered = list(filter(lambda x: x['type'] == 'audio', streams))
        return sorted(filtered, key=lambda x: RE_AUDIO_CODECS_PRIORITY.index(x['codec']))[0]['stream_no']


def run_in_shell(cmd):
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        out, err = process.communicate()
        if out:
            out = out.decode(ENCODING)
        if err:
            err = err.decode(ENCODING)
        return (process.returncode, out, err)


class Prober:
    def __init__(self, args):
        self.args = args
        self.file_name = self.extract_input_file_name()
        self._fmt = None
        self._streams = None

    def extract_input_file_name(self):
        i = 0
        for arg in self.args:
            i += 1
            if arg == '-i':
                return self.args[i]

    def get_data(self):
        if None in [self._fmt, self._streams]:
            cmd = ['/usr/bin/ffprobe', '-v', 'quiet', '-print_format',
                   'json', '-show_format', '-show_streams', self.file_name]
            # print(' '.join(cmd))
            json_str = run_in_shell(cmd)[1]
            output = json.loads(json_str)
            self._fmt = output['format']
            self._streams = output['streams']
        return self._fmt

    def get_duration(self):
        seconds = int(float(self.get_data()['duration']))
        return seconds

    def get_stream_language(self, stream):
        lang = None
        if 'tags' in stream and 'language' in stream['tags']:
            lang = stream['tags']['language']
        return lang

    def get_stream_bitrate(self, stream):
        bitrate = None
        if 'bit_rate' in stream:
            bitrate = int(stream['bit_rate'])
        return bitrate

    def get_audio_streams(self):
        streams = []
        self.get_data()
        audio_i = 0
        for stream in self._streams:
            if stream['codec_type'] == 'audio':
                media = {
                    'stream_no': audio_i,
                    'language': self.get_stream_language(stream),
                    'type': stream['codec_type'],
                    'codec': stream['codec_name'],
                    'bitrate': self.get_stream_bitrate(stream)
                }
                streams.append(media)
                audio_i += 1
        return streams

    def get_best_audio_stream(self):
        streams = self.get_audio_streams()
        filtered = list(filter(lambda x: x['type'] == 'audio', streams))
        return sorted(filtered, key=lambda x: RE_AUDIO_CODECS_PRIORITY.index(x['codec']))[0]


class KDialogProgressBar:
    def __init__(self, bus_name=PFF_BUS_NAME, object_path=PFF_OBJECT_PATH):
        self.bus_name = bus_name
        self.object_path = object_path
        self.props_mgr = None
        self.proxy = None
        self.reuse = True
        self.initial_value = 0

    def open(self, max_progress, label=None):
        if None in [self.bus_name, self.object_path]:
            cmd = ['/usr/bin/kdialog', '--progressbar', 'Progress', str(max_progress)]
            self.bus_name, self.object_path = [x.strip() for x in run_in_shell(cmd)[1].split(' ')]
            self.reuse = False
        self.proxy = dbus.SessionBus().get_object(self.bus_name, self.object_path)
        self.props_mgr = dbus.Interface(self.proxy, DBUS_PROPS)
        self.props_mgr.Set(PROGRESS_DIALOG, 'autoClose', True)
        if label:
            dialog = dbus.Interface(self.proxy, PROGRESS_DIALOG)
            dialog.setLabelText(KDialogProgressBar.format_label_text(label))
        if self.reuse:
            self.initial_value = max(0, self.props_mgr.Get(PROGRESS_DIALOG, 'value'))

    def update(self, seconds, label=None):
        seconds += self.initial_value
        self.props_mgr.Set(PROGRESS_DIALOG, 'value', seconds)
        if label:
            dialog = dbus.Interface(self.proxy, PROGRESS_DIALOG)
            dialog.setLabelText(KDialogProgressBar.format_label_text(label))

    def close(self):
        if not self.reuse:
            try:
                self.proxy.close()
            except Exception:
                pass

    @staticmethod
    def format_label_text(text):
        return '  ' + text + '  '
