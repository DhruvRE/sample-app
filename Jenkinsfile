pipeline {
    agent any

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: 'main']],
                          userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}", "app")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}:${env.BUILD_NUMBER}").push()
                    }
                }
            }
        }

        stage('Update Deployment Manifest') {
            steps {
                script {
                    sh """
                    sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml

                    git config user.email "jenkins@local"
                    git config user.name "Jenkins CI"
                    git add manifests/deployment.yaml
                    git commit -m "Update image tag to ${BUILD_NUMBER}" || echo "No changes to commit"
                    git push https://${GIT_CREDENTIALS}@${GIT_REPO#https://}
                    """
                }
            }
        }
    }
}
