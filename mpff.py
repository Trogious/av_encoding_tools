#!/usr/bin/env python3
import os
import sys

from tools import Prober, run_in_shell

VALID_EXTENSIONS = ['mkv', 'm2ts', 'mp4']


def usage():
    print('Usage: ' + sys.argv[0] + ' <fiele1> [file2] ...\n')


def main():
    if len(sys.argv) < 2:
        usage()
    else:
        total_duration = 0
        for arg in sys.argv[1:]:
            i = arg.rfind('.')
            if arg[i+1:] in VALID_EXTENSIONS and os.path.isfile(arg):
                total_duration += Prober(['-i', arg]).get_duration()
        name, path = [x.strip() for x in run_in_shell(
            ['/usr/bin/kdialog', '--progressbar', 'Progress', str(total_duration)])[1].split(' ')]
        print('export PFF_OBJECT_PATH=%s PFF_BUS_NAME=%s' % (path, name))


if __name__ == '__main__':
    main()
