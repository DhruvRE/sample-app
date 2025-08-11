pipeline {
    agent any

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"  // username+token credentials in Jenkins
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
    }

    triggers {
        githubPush()
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
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                usernameVariable: 'GIT_USER',
                                                passwordVariable: 'GIT_TOKEN')]) {
                    script {
                        sh """
                        sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml

                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"

                        git add manifests/deployment.yaml
                        git commit -m "Update image tag to ${BUILD_NUMBER}" || echo "No changes to commit"

                        git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git
                        
                        git pull --rebase origin main || echo "No remote changes to rebase"

                        git push origin main

                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        """
                    }
                }
            }
        }
    }
}
