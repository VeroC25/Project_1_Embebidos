SUMMARY = "Imagen Yocto para el sistema de control de acceso"

LICENSE = "MIT"

inherit core-image

IMAGE_INSTALL += " \
    packagegroup-core-boot \
    openssh \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-python \
    libcamera \
    libcamera-gst \
    gstreamer1.0-plugins-ugly-x264 \
    python3 \
    python3-pygobject \
    python3-numpy \
    python3-opencv \
    v4l-utils \
    control-acceso \
"

IMAGE_FEATURES += "ssh-server-openssh"

IMAGE_ROOTFS_EXTRA_SPACE = "2097152"
