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
        // DESACTIVADO TEMPORALMENTE
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
        // DESACTIVADO TEMPORALMENTE
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
        // DESACTIVADO TEMPORALMENTE
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
        // A4 - QEMU
        // DESACTIVADO TEMPORALMENTE
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
        // A5 - QEMU
        // DESACTIVADO TEMPORALMENTE
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
        // A6 - QEMU
        // DESACTIVADO TEMPORALMENTE
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
        // SMOKE TESTS
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
