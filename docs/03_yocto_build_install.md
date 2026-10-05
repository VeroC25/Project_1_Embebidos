# Yocto: construcción e instalación

## 1. Versiones fijadas

El proyecto utiliza ramas Scarthgap con revisiones exactas almacenadas en `yocto-config/versiones.txt`.

| Capa | Commit |
|---|---|
| poky | `cbd62bb2a9f2ab3466a0f72f4289bc86ca20a019` |
| meta-openembedded | `b5874ea07d69919d9b40d59f2c2f0bbd24bc3259` |
| meta-raspberrypi | `6ca1f75017cc5d5acdb8bb05634c4bc01fa049fd` |

Plataforma:

```text
MACHINE = "raspberrypi4-64"
INIT_MANAGER = "systemd"
```

## 2. Configuración específica de la cámara

La configuración del proyecto incluye:

```bitbake
VIDEO_CAMERA = "0"
RPI_KERNEL_DEVICETREE_OVERLAYS:append = " overlays/ov5647.dtbo"
RPI_EXTRA_CONFIG:append = "\ncamera_auto_detect=0\ndtoverlay=ov5647"
```

Esto evita depender del modo legacy de cámara y carga explícitamente el overlay OV5647.

## 3. Dependencias principales de la imagen

La receta `control-acceso-image.bb` incluye, entre otros:

```text
openssh
gstreamer1.0
gstreamer1.0-plugins-base
gstreamer1.0-plugins-good
gstreamer1.0-plugins-bad
gstreamer1.0-python
libcamera
libcamera-gst
gstreamer1.0-plugins-ugly-x264
python3
python3-pygobject
python3-numpy
python3-opencv
v4l-utils
control-acceso
```

## 4. Servicio systemd

El paquete instala:

```text
/usr/bin/control-acceso
/usr/lib/systemd/system/control-acceso.service
/etc/default/control-acceso
/var/lib/control-acceso
```

El servicio:

- arranca automáticamente;
- utiliza `/var/lib/control-acceso` como directorio de trabajo;
- reinicia ante fallo;
- espera 5 s antes de reiniciar.

## 5. Entrar al entorno de build

Entorno validado:

```bash
cd ~/proyecto-yocto-rpi/poky
source buildtools/environment-setup-x86_64-pokysdk-linux
source oe-init-build-env ../build-rpi
```

### Nota para Ubuntu 26.04

En el host de desarrollo se observó una restricción AppArmor sobre user namespaces. Cuando BitBake falla por acceso a `/proc/self/uid_map`, se utilizó temporalmente:

```bash
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
```

No convertir este ajuste en permanente sin justificarlo.

## 6. Construcción

```bash
bitbake control-acceso-image
```

Una ejecución válida finaliza con un resumen equivalente a:

```text
Tasks Summary: ... all succeeded
```

La imagen queda en:

```text
tmp/deploy/images/raspberrypi4-64/
```

El enlace utilizado:

```text
control-acceso-image-raspberrypi4-64.rootfs.wic.bz2
```

## 7. Flasheo de microSD

### 7.1 Identificar dispositivo

```bash
lsblk
```

**Verificar con extremo cuidado** el dispositivo. En el montaje de desarrollo la microSD apareció como `/dev/sda`, pero esto no debe asumirse en otra computadora.

### 7.2 Desmontar

Ejemplo:

```bash
sudo umount /dev/sda1
sudo umount /dev/sda2 2>/dev/null || true
```

### 7.3 Grabar

```bash
bzcat tmp/deploy/images/raspberrypi4-64/control-acceso-image-raspberrypi4-64.rootfs.wic.bz2 | \
sudo dd of=/dev/sda bs=4M status=progress conv=fsync
```

Luego:

```bash
sync
sudo eject /dev/sda
```

## 8. Primer arranque

Conectar:

- microSD;
- cámara OV5647;
- Ethernet;
- ventilación;
- alimentación.

Desde la laptop:

```bash
ip neigh
ping -c 3 10.42.0.X
ssh root@10.42.0.X
```

Si se reflasheó la microSD y SSH reporta una host key distinta:

```bash
ssh-keygen -f ~/.ssh/known_hosts -R 10.42.0.X
```

## 9. Configurar destino RTP

Editar:

```text
/etc/default/control-acceso
```

Ejemplo de laboratorio:

```text
CONTROL_ACCESO_MODE=rpi
CONTROL_ACCESO_GUI=0
DEST_HOST=10.42.0.1
DEST_PORT=5000
```

Reiniciar:

```bash
systemctl restart control-acceso
journalctl -u control-acceso -n 40 --no-pager
```

## 10. Comprobaciones básicas

```bash
systemctl status control-acceso --no-pager
cam -l
gst-inspect-1.0 libcamerasrc
gst-inspect-1.0 x264enc
```

Comprobar almacenamiento:

```bash
ls -lh /var/lib/control-acceso/evidencias
tail -n 10 /var/lib/control-acceso/bitacora_accesos.log
```

## 11. Reproducibilidad pendiente

Antes del cierre final del proyecto conviene ejecutar al menos una reconstrucción documentada desde un entorno limpio o sin reutilizar resultados que oculten dependencias no declaradas.
