/* Requires the Docker Pipeline plugin */
pipeline {
    agent { docker { image 'python:3.13.2-alpine3.21' } }

    environment {
        TESTED = 'No Sir'
    }
    stages {
        stage('build') {
            steps {
                retry(2) {
                    sh 'python --version'
                }
                echo "Is our code tested yet? Answer: ${TESTED}"
            }
            stage('Test') {
                steps {
                    echo 'Testing'
                }
            }
            stage('Deploy') {
                steps {
                    echo 'Deploying'
                }
            }
            timeout(time: 1, unit: "MINUTES"){
                echo 'Python is not installed or smthn'
            }
        }
    }
    post {
        always {
            junit 'build/reports/**/*.xml'
        }
        success {
            echo 'The Jenkins run was successful!'
        }
        failure {
            echo 'The Jenkins run was unsuccessful :('
        }
    }
}
