#!/usr/bin/env python3
import sys


def main():
    a_len = len(sys.argv)
    if a_len < 2:
        print('Usage: ' + sys.argv[0] + ' <[[[H]H:]mm:]ss>\n')
    else:
        hms = [int(x) for x in reversed(sys.argv[1].split(':'))]
        MULTIPLIERS = [1, 60, 3600]
        seconds = 0
        for i in range(len(hms)):
            seconds += hms[i] * MULTIPLIERS[i]
        print(seconds)


if __name__ == '__main__':
    main()
