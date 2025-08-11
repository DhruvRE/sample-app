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
                    sh "sed -i 's|image: .*|image: ${DOCKER_IMAGE}:${env.BUILD_NUMBER}|' k8s-deploy.yaml"
                }
            }
        }

        stage('Commit & Push Changes') {
            steps {
                script {
                    // Use Jenkins stored Git credentials to authenticate the shell git push
                    withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                      usernameVariable: 'GIT_USER',
                                                      passwordVariable: 'GIT_TOKEN')]) {
                        // single-quoted block so shell variables ($GIT_USER, $GIT_TOKEN, $BUILD_NUMBER) are expanded in shell
                        sh '''
                            git config user.email "jenkins@local"
                            git config user.name "Jenkins CI"
                            git add k8s-deploy.yaml
                            git commit -m "Update image tag to $BUILD_NUMBER" || echo "No changes to commit"

                            # Temporarily set remote to include credentials for this push only
                            git remote set-url origin https://$GIT_USER:$GIT_TOKEN@github.com/DhruvRE/sample-app.git

                            # Push changes
                            git push origin main

                            # Restore remote to the credential-less URL
                            git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        '''
                    }
                }
            }
        }
    }
}
