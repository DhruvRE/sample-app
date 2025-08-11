pipeline {
    agent any

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"   // must be "Username with password" (username = your GH user, password = PAT)
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
    }
    
    stages {
        stage('Checkout') {
            steps {
                git credentialsId: env.GIT_CREDENTIALS, url: env.GIT_REPO, branch: 'main'
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
                        docker.image("${DOCKER_IMAGE}:${env.BUILD_NUMBER}").push("latest")
                    }
                }
            }
        }

        stage('Update Kubernetes Manifest') {
            steps {
                script {
                    // Replace only REPLACE_TAG in the manifest
                    sh "sed -i 's|REPLACE_TAG|${BUILD_NUMBER}|' manifests/k8s-deploy.yaml"
                }
            }
        }

        stage('Commit & Push Changes') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                    usernameVariable: 'GIT_USER',
                                                    passwordVariable: 'GIT_TOKEN')]) {
                        sh '''
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"
                        git add manifests/k8s-deploy.yaml
                        git commit -m "Update image tag to $BUILD_NUMBER" || echo "No changes to commit"

                        git remote set-url origin https://$GIT_USER:$GIT_TOKEN@github.com/DhruvRE/sample-app.git
                        git push origin main
                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        '''
                    }
                }
            }
        }

    }
}
