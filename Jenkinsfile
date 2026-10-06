pipeline {
    agent any

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
