#!/bin/sh


# rtsp stream

# . .venv/bin/activate && RTSP_URL="rtsp://username:password@ipaddress:554/av_stream/ch0" python3 detect_picam_rtsp.py


# picam stream ( cam0 on cm-5 )

. .venv/bin/activate && USE_PICAM=1 python detect_picam_rtsp.py
