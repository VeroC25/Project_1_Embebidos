
#!/bin/bash
set -euo pipefail

# Recibir el flujo RTP/H.264 y medir los FPS decodificados.
exec gst-launch-1.0 -v \
    udpsrc port=5000 \
        caps="application/x-rtp,media=video,encoding-name=H264,payload=96,clock-rate=90000" ! \
    rtpjitterbuffer latency=100 ! \
    rtph264depay ! \
    avdec_h264 ! \
    fpsdisplaysink name=fps \
        video-sink=fakesink \
        text-overlay=false \
        sync=false \
        fps-update-interval=1000
