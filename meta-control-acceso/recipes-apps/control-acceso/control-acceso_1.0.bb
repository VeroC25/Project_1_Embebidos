SUMMARY = "Aplicacion Python para el sistema de control de acceso"
DESCRIPTION = "Aplicacion integrada con GStreamer, OpenCV y lectura de codigos QR"
LICENSE = "CLOSED"

SRC_URI = " \
    file://prueba_integrada_h1.py \
    file://control-acceso.service \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = " \
    python3-core \
    python3-pygobject \
    python3-numpy \
    python3-opencv \
    gstreamer1.0 \
    gstreamer1.0-python \
    libcamera-gst \
    gstreamer1.0-plugins-ugly-x264 \
"

CONTROL_ACCESO_MODE = "rpi"
CONTROL_ACCESO_MODE:qemux86-64 = "qemu"

SYSTEMD_SERVICE:${PN} = "control-acceso.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install() {
    # Aplicacion
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/prueba_integrada_h1.py \
        ${D}${bindir}/control-acceso

    # Servicio systemd
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/control-acceso.service \
        ${D}${systemd_system_unitdir}/control-acceso.service

    # Configuracion de ejecucion
    install -d ${D}${sysconfdir}/default

    echo "CONTROL_ACCESO_MODE=${CONTROL_ACCESO_MODE}" \
        > ${D}${sysconfdir}/default/control-acceso

    echo "CONTROL_ACCESO_GUI=0" \
        >> ${D}${sysconfdir}/default/control-acceso

    echo "DEST_HOST=127.0.0.1" \
        >> ${D}${sysconfdir}/default/control-acceso

    echo "DEST_PORT=5000" \
        >> ${D}${sysconfdir}/default/control-acceso

    # Directorio persistente de trabajo
    install -d ${D}${localstatedir}/lib/control-acceso
}

FILES:${PN} += " \
    ${bindir}/control-acceso \
    ${systemd_system_unitdir}/control-acceso.service \
    ${sysconfdir}/default/control-acceso \
    ${localstatedir}/lib/control-acceso \
"
