#!/bin/sh -

if [ $# -lt 2 ]; then
    echo "Syntax: $0 <in_file> <out_file> [start_time_secs] [audio_track_no]"
    exit 1
fi

IN_FILE="$1"
OUT_FILE="$2"
if [ ! -s "$IN_FILE" ]; then
    echo "No such file: $IN_FILE"
    exit 1
fi

if [ $# -gt 2 ]; then
    START_SECS="$3"
else
    START_SECS=600
fi

if [ $# -gt 3 ]; then
    AUDIO_TRACK_NO="$4"
else
    AUDIO_TRACK_NO=0
fi

NICE='/usr/bin/nice'
FFMPEG=/usr/bin/ffmpeg
#OUT_FILE=./`echo $OUT_FILE | sed 's/\.mkv/_sample.mkv/' | sed 's/\.m2ts/_sample.mkv/' | sed 's/\.mp4/_sample.mkv/'`
DURATION_SECS=120
LOG_LEVEL='-loglevel info'
OVERWRITE='-y'
#NTS=''
NTS='-avoid_negative_ts 1'
#CONTAINERS='mkv mp4 avi'
#CONTAINERS='mp4 avi mov wmv m4v'
CONTAINERS='mkv'


for container in $CONTAINERS
do
    #OUT_FILE_CONTAINER=`echo $OUT_FILE | sed "s/\.mkv$/\.${container}/"`
    OUT_FILE_CONTAINER=$OUT_FILE
    CMD="$NICE -n +19 $FFMPEG $LOG_LEVEL -hwaccel cuvid -ss $START_SECS -t $DURATION_SECS -i $IN_FILE $TIME -map_metadata -1 -c:v copy -map 0:v:0 -c:a copy -map 0:a:$AUDIO_TRACK_NO -sn $NTS $OVERWRITE $OUT_FILE_CONTAINER"
    echo $CMD
    echo
    $CMD
done
