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

        stage('Validar retencion H7') {
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

        stage('Ejecutar pruebas') {
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
        success {
            echo 'Todas las pruebas terminaron correctamente.'
        }

        failure {
            echo 'Fallo la integracion. Revisar el registro.'
        }
    }
}
