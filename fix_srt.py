import datetime


def get_delta(tstamp):
    sm = tstamp.split(',')
    hms = [int(x) for x in sm[0].split(':')]
    delta = datetime.timedelta(hours=hms[0], minutes=hms[1], seconds=hms[2], milliseconds=int(sm[1]))
    return delta


def str_delta(delta):
    s = '0' + str(delta)
    s = s[:12].replace('.', ',')
    return s


start_times = []

with open('subs.srt', 'r') as f_in:
    lines = f_in.readlines()
    for line in lines:
        if ' --> ' in line:
            start, _ = line.split(' --> ')
            start_times.append(get_delta(start))
    start_times.append(start_times[-1] + datetime.timedelta(seconds=10))

    with open('out_subs.srt', 'w') as f_out:
        i = 0
        for line in lines:
            line = line.strip()
            if ' --> ' in line:
                start, end = line.split(' --> ')
                delta = get_delta(start)
                delta = delta + datetime.timedelta(seconds=5)
                if delta < start_times[i+1]:
                    end = str_delta(delta)
                else:
                    end = str_delta(start_times[i+1])
                f_out.write('%s --> %s\n' % (start, end))
                i += 1
            else:
                f_out.write(line + '\n')
