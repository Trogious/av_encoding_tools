import json
import re
import subprocess

import dbus

ENCODING = 'utf8'
RE_BITRATE = re.compile('bitrate: \\d+ [a-zA-Z]')
# Stream #0:0(eng): Video: h264
RE_STREAM = re.compile('Stream #\\d:\\d\\([a-z][a-z][a-z]\\): [a-zA-Z0-9_]+: [a-zA-Z0-9_]+')
RE_AUDIO_CODECS_PRIORITY = ['truehd', 'dts', 'aac', 'ac3', 'mp3']


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

    def get_streams(self):
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

    def get_best_audio_source(self):
        streams = self.get_streams()
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

    def extract_input_file_name(self):
        i = 0
        for arg in self.args:
            i += 1
            if arg == '-i':
                return self.args[i]

    def get_format_data(self):
        if not self._fmt:
            cmd = ['/usr/bin/ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', self.file_name]
            json_str = run_in_shell(cmd)[1]
            fmt = json.loads(json_str)
            self._fmt = fmt['format']
        return self._fmt

    def get_duration(self):
        seconds = int(float(self.get_format_data()['duration']))
        return seconds


class KDialogProgressBar:
    def __init__(self):
        self.bus_name = None
        self.object_path = None
        self.props_mgr = None
        self.proxy = None

    def open(self, max_progress, label=None):
        cmd = ['/usr/bin/kdialog', '--progressbar', 'test', str(max_progress)]
        self.bus_name, self.object_path = [x.strip() for x in run_in_shell(cmd)[1].split(' ')]
        bus = dbus.SessionBus()
        self.proxy = bus.get_object(self.bus_name, self.object_path)
        self.props_mgr = dbus.Interface(self.proxy, 'org.freedesktop.DBus.Properties')
        self.props_mgr.Set('org.kde.kdialog.ProgressDialog', 'autoClose', True)
        if label:
            dialog = dbus.Interface(self.proxy, 'org.kde.kdialog.ProgressDialog')
            dialog.setLabelText(KDialogProgressBar.format_label_text(label))

    def update(self, seconds, label=None):
        self.props_mgr.Set('org.kde.kdialog.ProgressDialog', 'value', seconds)
        if label:
            dialog = dbus.Interface(self.proxy, 'org.kde.kdialog.ProgressDialog')
            dialog.setLabelText(KDialogProgressBar.format_label_text(label))

    def close(self):
        self.proxy.close()

    @staticmethod
    def format_label_text(text):
        return '  ' + text + '  '
