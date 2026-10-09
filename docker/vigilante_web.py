
#!/usr/bin/env python3

import gi
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

# Almacenar únicamente el último frame JPEG recibido.
condicion = threading.Condition()
ultimo_frame = None
numero_frame = 0


def recibir_frame(appsink):
    global ultimo_frame, numero_frame

    # Obtener el frame JPEG generado por GStreamer.
    muestra = appsink.emit("pull-sample")

    if muestra is None:
        return Gst.FlowReturn.ERROR

    buffer = muestra.get_buffer()
    correcto, datos = buffer.map(Gst.MapFlags.READ)

    if not correcto:
        return Gst.FlowReturn.ERROR

    try:
        frame = bytes(datos.data)
    finally:
        buffer.unmap(datos)

    # Actualizar el frame disponible para el navegador.
    with condicion:
        ultimo_frame = frame
        numero_frame += 1
        condicion.notify_all()

    return Gst.FlowReturn.OK


class ServidorVigilante(BaseHTTPRequestHandler):

    def do_GET(self):

        # Página principal del vigilante.
        if self.path == "/":
            pagina = b"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Estacion del vigilante</title>
                <style>
                    body {
                        background: #171c25;
                        color: white;
                        font-family: Arial, sans-serif;
                        text-align: center;
                    }
                    img {
                        width: 90%;
                        max-width: 1280px;
                        border: 2px solid #46a778;
                    }
                </style>
            </head>
            <body>
                <h1>Sistema de control de acceso</h1>
                <h2>Estacion del vigilante</h2>
                <img src="/video.mjpg" alt="Video en vivo">
            </body>
            </html>
            """

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(pagina)))
            self.end_headers()
            self.wfile.write(pagina)
            return

        # Transmisión MJPEG hacia el navegador.
        if self.path == "/video.mjpg":
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=frame"
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            anterior = -1

            try:
                while True:
                    with condicion:
                        condicion.wait_for(
                            lambda: numero_frame != anterior,
                            timeout=5
                        )

                        frame = ultimo_frame
                        anterior = numero_frame

                    if frame is None:
                        continue

                    self.wfile.write(
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: "
                        + str(len(frame)).encode()
                        + b"\r\n\r\n"
                        + frame
                        + b"\r\n"
                    )

            except (BrokenPipeError, ConnectionResetError):
                pass

            return

        self.send_error(404)


# Pipeline receptor: RTP/H.264 hacia imágenes JPEG.
pipeline = Gst.parse_launch(
    "udpsrc port=5000 "
    'caps="application/x-rtp,media=video,'
    'encoding-name=H264,payload=96,clock-rate=90000" ! '
    "rtpjitterbuffer latency=100 ! "
    "rtph264depay ! "
    "avdec_h264 ! "
    "videoconvert ! "
    "video/x-raw,format=I420 ! "
    "jpegenc quality=75 ! "
    "appsink name=jpeg_sink emit-signals=true "
    "max-buffers=1 drop=true sync=false"
)

appsink = pipeline.get_by_name("jpeg_sink")
appsink.connect("new-sample", recibir_frame)

servidor = ThreadingHTTPServer(
    ("0.0.0.0", 8081),
    ServidorVigilante
)

try:
    pipeline.set_state(Gst.State.PLAYING)

    print("Vigilante iniciado en el puerto 8081", flush=True)
    servidor.serve_forever()

finally:
    servidor.server_close()
    pipeline.set_state(Gst.State.NULL)
