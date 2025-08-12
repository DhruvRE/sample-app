pipeline {
    agent any

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: 'main']],
                          userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}")
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}:${env.BUILD_NUMBER}").push()
                    }
                }
            }
        }

        stage('Update K8s Manifest in GitOps Repo') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                     usernameVariable: 'GIT_USER',
                                                     passwordVariable: 'GIT_TOKEN')]) {
                        sh '''
                        git clone https://$GIT_USER:$GIT_TOKEN@github.com/DhruvRE/sample-app-deploy.git
                        cd sample-app-deploy
                        sed -i "s|REPLACE_TAG|${BUILD_NUMBER}|" k8s-deploy.yaml
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"
                        git commit -am "Update image tag to $BUILD_NUMBER" || echo "No changes to commit"
                        git push
                        '''
                    }
                }
            }
        }
    }
}
