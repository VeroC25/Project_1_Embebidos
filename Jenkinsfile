pipeline {
    agent any

    environment {
        RPI_HOST = 'root@10.42.0.113'
    }

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    stages {

        stage('Obtener codigo') {
            steps {
                checkout scm
            }
        }

        stage('Construir imagen Docker') {
            steps {
                sh 'docker build -t control-acceso-dev:ci .'
            }
        }

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

        stage('A1 - Caps negociados') {
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

        stage('A1 - Caps Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/A1_caps_rpi.log

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST"                             'systemctl start control-acceso'                             >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A1 a Raspberry..."

                    scp -o BatchMode=yes                         tests/rpi/test_a1_caps.sh                         "$RPI_HOST:/tmp/test_a1_caps.sh"

                    echo "Ejecutando A1 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso
                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados
                        chmod +x /tmp/test_a1_caps.sh
                        cd /tmp
                        ./test_a1_caps.sh rpi
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia..."

                    scp -o BatchMode=yes                         "$RPI_HOST:/tmp/resultados/A1_caps_rpi.log"                         resultados/A1_caps_rpi.log                         || true

                    exit "$TEST_STATUS"
                '''
            }
        }

        stage('A2 - Formato de pixel') {
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

        stage('A2 - Formato Raspberry real') {
            steps {
                sh '''
                    set -eu

                    mkdir -p resultados
                    rm -f resultados/A2_formato_rpi.log

                    cleanup_rpi() {
                        ssh -o BatchMode=yes "$RPI_HOST"                             'systemctl start control-acceso'                             >/dev/null 2>&1 || true
                    }

                    trap cleanup_rpi EXIT

                    echo "Copiando A2 a Raspberry..."

                    scp -o BatchMode=yes                         tests/rpi/test_a2_pixel_format.sh                         "$RPI_HOST:/tmp/test_a2_pixel_format.sh"

                    echo "Ejecutando A2 sobre Raspberry Pi real..."

                    set +e

                    ssh -o BatchMode=yes "$RPI_HOST" '
                        systemctl stop control-acceso
                        rm -rf /tmp/resultados
                        mkdir -p /tmp/resultados
                        chmod +x /tmp/test_a2_pixel_format.sh
                        cd /tmp
                        ./test_a2_pixel_format.sh rpi x264enc
                    '

                    TEST_STATUS=$?

                    set -e

                    echo "Recuperando evidencia A2..."

                    scp -o BatchMode=yes                         "$RPI_HOST:/tmp/resultados/A2_formato_rpi.log"                         resultados/A2_formato_rpi.log                         || true

                    exit "$TEST_STATUS"
                '''
            }
        }

        stage('A3 - Framerate real') {
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

        stage('A4 - Capsfilters') {
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

        stage('A5 - Conversiones') {
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

        stage('A6 - Grafo pipeline') {
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

        stage('Probar comunicacion Docker') {
            steps {
                sh 'bash scripts/test_compose.sh'
            }
        }
    }

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
