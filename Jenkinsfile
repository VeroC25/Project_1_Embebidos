pipeline {
    agent any

    environment {
        RPI_HOST = 'root@10.42.0.113'

        // Las pruebas A1-A6 de QEMU quedan desactivadas.
        // Para volver a habilitarlas, cambiar false por true.
        RUN_QEMU = 'false'
    }

    options {
        skipDefaultCheckout(true)
        timestamps()

        // Evita que dos builds utilicen la Raspberry al mismo tiempo.
        disableConcurrentBuilds()
    }

    stages {

        // ============================================================
        // OBTENER CODIGO
        // ============================================================

        stage('Obtener codigo') {
            steps {
                checkout scm
            }
        }


        // ============================================================
        // CONSTRUIR IMAGEN DOCKER
        // ============================================================

        stage('Construir imagen Docker') {
            steps {
                sh 'docker build -t control-acceso-dev:ci .'
            }
        }


        // ============================================================
        // PRUEBAS GENERALES DEL REPOSITORIO
        // ============================================================

        stage('Validar repositorio') {
            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash tests/host/test_repo_consistency.sh
                '''
            }
        }


        stage('H7 - Retencion') {
            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        python3 tests/host/test_retention.py
                '''
            }
        }


        stage('E3 - Error fatal') {
            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash tests/host/test_error_fatal.sh
                '''
            }
        }


        // ============================================================
        // A1 - QEMU
        // ============================================================

        stage('A1 - Caps negociados QEMU') {
            when {
                expression {
                    env.RUN_QEMU == 'true'
                }
            }

            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash tests/rpi/test_a1_caps.sh qemu
                '''
            }
        }


        // ============================================================
        // A1 - RASPBERRY PI REAL
        // ============================================================

        stage('A1 - Caps Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/A1_caps_rpi.log

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A1 a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_a1_caps.sh \
                        "$RPI_HOST:/tmp/test_a1_caps.sh"

                    echo "Ejecutando A1 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso

                        mkdir -p /tmp/resultados
                        rm -f /tmp/resultados/A1_caps_rpi.log

                        chmod +x /tmp/test_a1_caps.sh

                        cd /tmp

                        ./test_a1_caps.sh rpi
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia A1..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A1_caps_rpi.log" \
                        resultados/A1_caps_rpi.log \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // A2 - QEMU
        // ============================================================

        stage('A2 - Formato de pixel QEMU') {
            when {
                expression {
                    env.RUN_QEMU == 'true'
                }
            }

            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash tests/rpi/test_a2_pixel_format.sh qemu
                '''
            }
        }


        // ============================================================
        // A2 - RASPBERRY PI REAL
        // ============================================================

        stage('A2 - Formato Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/A2_formato_rpi.log

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A2 a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_a2_pixel_format.sh \
                        "$RPI_HOST:/tmp/test_a2_pixel_format.sh"

                    echo "Ejecutando A2 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso

                        mkdir -p /tmp/resultados
                        rm -f /tmp/resultados/A2_formato_rpi.log

                        chmod +x /tmp/test_a2_pixel_format.sh

                        cd /tmp

                        ./test_a2_pixel_format.sh rpi x264enc
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia A2..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A2_formato_rpi.log" \
                        resultados/A2_formato_rpi.log \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // A3 - QEMU
        // ============================================================

        stage('A3 - Framerate QEMU') {
            when {
                expression {
                    env.RUN_QEMU == 'true'
                }
            }

            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        python3 tests/rpi/test_a3_framerate.py qemu 10
                '''
            }
        }


        // ============================================================
        // A3 - RASPBERRY PI REAL
        // ============================================================

        stage('A3 - Framerate Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/A3_framerate_rpi.txt

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A3 a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_a3_framerate.py \
                        "$RPI_HOST:/tmp/test_a3_framerate.py"

                    echo "Ejecutando A3 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso

                        mkdir -p /tmp/resultados
                        rm -f /tmp/resultados/A3_framerate_rpi.txt

                        cd /tmp

                        python3 /tmp/test_a3_framerate.py rpi 10
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia A3..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A3_framerate_rpi.txt" \
                        resultados/A3_framerate_rpi.txt \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // A4 - QEMU
        // ============================================================

        stage('A4 - Capsfilters QEMU') {
            when {
                expression {
                    env.RUN_QEMU == 'true'
                }
            }

            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        python3 tests/rpi/test_a4_capsfilters.py qemu
                '''
            }
        }


        // ============================================================
        // A4 - RASPBERRY PI REAL
        // ============================================================

        stage('A4 - Capsfilters Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/A4_capsfilters_rpi.txt

                    echo "Copiando A4 y aplicacion a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_a4_capsfilters.py \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando A4 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        cd /tmp

                        python3 /tmp/test_a4_capsfilters.py rpi NV12
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia A4..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A4_capsfilters_rpi.txt" \
                        resultados/A4_capsfilters_rpi.txt \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // A5 - QEMU
        // ============================================================

        stage('A5 - Conversiones QEMU') {
            when {
                expression {
                    env.RUN_QEMU == 'true'
                }
            }

            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash tests/rpi/test_a5_conversions.sh qemu
                '''
            }
        }


        // ============================================================
        // A5 - RASPBERRY PI REAL
        // ============================================================

        stage('A5 - Conversiones Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados

                    rm -f resultados/A5_pipeline_rpi.log
                    rm -f resultados/A5_conversiones_rpi.txt
                    rm -f resultados/A5_pipeline_rpi.dot

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A5 y aplicacion a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_a5_conversions.sh \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando A5 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso

                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        chmod +x /tmp/test_a5_conversions.sh

                        cd /tmp

                        ./test_a5_conversions.sh rpi
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencias A5..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A5_pipeline_rpi.log" \
                        resultados/A5_pipeline_rpi.log \
                        || true

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A5_conversiones_rpi.txt" \
                        resultados/A5_conversiones_rpi.txt \
                        || true

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A5_pipeline_rpi.dot" \
                        resultados/A5_pipeline_rpi.dot \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // A6 - QEMU
        // ============================================================

        stage('A6 - Grafo pipeline QEMU') {
            when {
                expression {
                    env.RUN_QEMU == 'true'
                }
            }

            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash tests/rpi/test_a6_pipeline_graph.sh qemu
                '''
            }
        }


        // ============================================================
        // A6 - RASPBERRY PI REAL
        // ============================================================

        stage('A6 - Grafo Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados

                    rm -f resultados/A6_pipeline_rpi.log
                    rm -f resultados/A6_revision_rpi.txt
                    rm -f resultados/A6_pipeline_rpi.dot

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A6 y aplicacion a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_a6_pipeline_graph.sh \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando A6 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso

                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        chmod +x /tmp/test_a6_pipeline_graph.sh

                        cd /tmp

                        ./test_a6_pipeline_graph.sh rpi
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencias A6..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A6_pipeline_rpi.log" \
                        resultados/A6_pipeline_rpi.log \
                        || true

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A6_revision_rpi.txt" \
                        resultados/A6_revision_rpi.txt \
                        || true

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/A6_pipeline_rpi.dot" \
                        resultados/A6_pipeline_rpi.dot \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // BLOQUE B - TOPOLOGIA Y FLUJO
        // ============================================================

        stage('B1-B6 - Topologia y flujo Raspberry') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados

                    rm -f resultados/B*.txt
                    rm -f resultados/B*.log

                    if [ ! -f resultados/A3_framerate_rpi.txt ]; then
                        echo "FAIL: falta evidencia A3 para obtener FPS real."
                        exit 1
                    fi

                    FPS="$(
                        awk '/Framerate real:/ {print $3}' \
                            resultados/A3_framerate_rpi.txt \
                        | tail -n 1
                    )"

                    if [ -z "$FPS" ]; then
                        echo "FAIL: no fue posible leer FPS real de A3."
                        exit 1
                    fi

                    echo "FPS real para B3/B5: $FPS"

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando pruebas B1-B6 a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_b1_tee_queues.py \
                        tests/rpi/test_b2_queue_policy.py \
                        tests/rpi/test_b3_queue_latency.py \
                        tests/rpi/test_b4_appsink.py \
                        tests/rpi/test_b5_callback.py \
                        tests/rpi/test_b6_eos_systemd.sh \
                        tests/rpi/run_block_b_rpi.sh \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando bloque B completo..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" "
                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        chmod +x \
                            /tmp/run_block_b_rpi.sh \
                            /tmp/test_b6_eos_systemd.sh

                        cd /tmp

                        ./run_block_b_rpi.sh '$FPS'
                    "

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencias del bloque B..."

                    scp -r -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/." \
                        resultados/ \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }



        // ============================================================
        // D3 - INTERVALO DE KEYFRAMES
        // ============================================================

        stage('D3 - Keyframes Raspberry') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/D3_keyframes_rpi.txt

                    if [ ! -f resultados/A3_framerate_rpi.txt ]; then
                        echo "FAIL: falta evidencia A3 para obtener FPS real."
                        exit 1
                    fi

                    FPS="$(
                        awk '/Framerate real:/ {print $3}' \
                            resultados/A3_framerate_rpi.txt \
                        | tail -n 1
                    )"

                    if [ -z "$FPS" ]; then
                        echo "FAIL: no fue posible leer FPS real de A3."
                        exit 1
                    fi

                    echo "FPS real para D3: $FPS"

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando D3 a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_d3_keyframes.py \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando D3..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" "
                        systemctl stop control-acceso

                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        cd /tmp

                        python3 test_d3_keyframes.py \
                            prueba_integrada_h1.py \
                            '$FPS'
                    "

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia D3..."

                    scp -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/D3_keyframes_rpi.txt" \
                        resultados/D3_keyframes_rpi.txt \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // E1 / E3 / E6 - MANEJO DE ERRORES Y RECUPERACION
        // G3 / G5 - REPRODUCIBILIDAD YOCTO
        // ============================================================

        stage('E1 E3 E6 G3 G5 - Validacion Raspberry') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados

                    rm -f resultados/E1_*.txt
                    rm -f resultados/E3_*.txt
                    rm -f resultados/E6_*.txt
                    rm -f resultados/G3_*.txt
                    rm -f resultados/G5_*.txt

                    echo "Copiando pruebas E/G a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_e1_bus_watch.py \
                        tests/rpi/test_e3_recovery_policy.sh \
                        tests/rpi/test_e6_systemd_restart.sh \
                        tests/rpi/test_g3_registry.sh \
                        tests/rpi/test_g5_versions.sh \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando pruebas E/G..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        chmod +x \
                            /tmp/test_e3_recovery_policy.sh \
                            /tmp/test_e6_systemd_restart.sh \
                            /tmp/test_g3_registry.sh \
                            /tmp/test_g5_versions.sh

                        cd /tmp

                        echo
                        echo "===== E1 ====="
                        python3 \
                            test_e1_bus_watch.py \
                            prueba_integrada_h1.py \
                            || exit 1

                        echo
                        echo "===== E3 ====="
                        ./test_e3_recovery_policy.sh \
                            || exit 1

                        echo
                        echo "===== E6 ====="
                        ./test_e6_systemd_restart.sh \
                            || exit 1

                        echo
                        echo "===== G3 ====="
                        ./test_g3_registry.sh \
                            || exit 1

                        echo
                        echo "===== G5 ====="
                        ./test_g5_versions.sh \
                            || exit 1
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencias E/G..."

                    scp -r -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/." \
                        resultados/ \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // BLOQUE C - HARDWARE VS SOFTWARE
        // ============================================================

        stage('C1-C4 - Hardware vs software Raspberry') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados

                    rm -f resultados/C*.txt
                    rm -f resultados/C*.log
                    rm -f resultados/C*.env

                    if [ ! -f resultados/A3_framerate_rpi.txt ]; then
                        echo "FAIL: falta A3 para obtener FPS real."
                        exit 1
                    fi

                    FPS="$(
                        awk '/Framerate real:/ {print $3}' \
                            resultados/A3_framerate_rpi.txt \
                        | tail -n 1
                    )"

                    if [ -z "$FPS" ]; then
                        echo "FAIL: no fue posible leer FPS de A3."
                        exit 1
                    fi

                    echo "FPS real para bloque C: $FPS"

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST" \
                            'systemctl start control-acceso' \
                            >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando pruebas C1-C4 a Raspberry..."

                    scp -o BatchMode=yes \
                        tests/rpi/test_c1_hw_encoder.sh \
                        tests/rpi/test_c2_cpu_compare.py \
                        tests/rpi/test_c3_hw_operating_point.sh \
                        tests/rpi/test_c4_dmabuf.sh \
                        tests/rpi/run_block_c_rpi.sh \
                        prueba_integrada_h1.py \
                        "$RPI_HOST:/tmp/"

                    echo "Ejecutando bloque C completo..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" "
                        systemctl stop control-acceso \
                            >/dev/null 2>&1 || true

                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados

                        chmod +x \
                            /tmp/test_c1_hw_encoder.sh \
                            /tmp/test_c3_hw_operating_point.sh \
                            /tmp/test_c4_dmabuf.sh \
                            /tmp/run_block_c_rpi.sh

                        cd /tmp

                        ./run_block_c_rpi.sh '$FPS'
                    "

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencias del bloque C..."

                    scp -r -o BatchMode=yes \
                        "$RPI_HOST:/tmp/resultados/." \
                        resultados/ \
                        || true

                    exit "$TEST_STATUS"
                '''
            }
        }


        // ============================================================
        // SMOKE TESTS
        // ============================================================

        stage('Ejecutar smoke tests') {
            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --mount type=bind,src="$WORKSPACE",dst=/proyecto \
                        -w /proyecto \
                        control-acceso-dev:ci \
                        bash scripts/smoke_test.sh
                '''
            }
        }


        // ============================================================
        // COMUNICACION ENTRE CONTENEDORES
        // ============================================================

        stage('Probar comunicacion Docker') {
            steps {
                sh 'bash scripts/test_compose.sh'
            }
        }
    }


    // ================================================================
    // RESULTADOS
    // ================================================================

    post {

        always {
            archiveArtifacts(
                artifacts: 'resultados/**/*',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }

        success {
            echo 'Todas las pruebas terminaron correctamente.'
        }

        failure {
            echo 'Fallo la integracion. Revisar el registro.'
        }
    }
}
