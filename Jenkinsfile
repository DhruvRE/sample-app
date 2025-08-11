pipeline {
    agent any

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
    }

    triggers {
        // Poll only dbranch every 5 minutes (or use GitHub webhook but filter branch)
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: 'refs/heads/dbranch']],
                          userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
            }
        }

        stage('Skip CI if commit says so') {
            steps {
                script {
                    def lastCommitMsg = sh(script: "git log -1 --pretty=%B", returnStdout: true).trim()
                    if (lastCommitMsg.contains("[ci skip]")) {
                        echo "Build skipped due to [ci skip] tag in commit message."
                        currentBuild.result = 'SUCCESS'
                        error("Skipping build")
                    }
                }
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

        stage('Merge dbranch into main') {
            steps {
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    script {
                        sh """
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"
                        git fetch origin main
                        git checkout main
                        git pull origin main
                        git merge dbranch --no-ff -m "Merge dbranch into main [ci skip]"
                        git push https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git main
                        """
                    }
                }
            }
        }

        // Optional: You can do deployment manifest update manually on main branch or in a separate job.
        // Avoid doing it automatically here to prevent looping.
        stage('Cleanup Old Docker Images') {
            steps {
                script {
                    sh '''
                        echo "Cleaning up old docker images for ${DOCKER_IMAGE}..."
                        docker images --format "{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}" | \
                        grep "^${DOCKER_IMAGE} " | \
                        sort -k4 -r | \
                        awk 'NR>5 { print $3 }' | \
                        xargs -r docker rmi || true
                    '''
                }
            }
        }
    }
}
