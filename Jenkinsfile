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

        stage('Check Commit Message') {
            steps {
                script {
                    // Get the last commit message
                    env.GIT_COMMIT_MESSAGE = sh(
                        script: "git log -1 --pretty=%B",
                        returnStdout: true
                    ).trim()
                    echo "Commit message: '${env.GIT_COMMIT_MESSAGE}'"
                }
            }
        }

        stage('Build Docker Image') {
            when {
                expression {
                    // Skip if commit message contains [skip ci]
                    return !env.GIT_COMMIT_MESSAGE.contains('[skip ci]')
                }
            }
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}", "app")
                }
            }
        }

        stage('Push Docker Image') {
            when {
                expression {
                    // Skip if commit message contains [skip ci]
                    return !env.GIT_COMMIT_MESSAGE.contains('[skip ci]')
                }
            }
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}:${env.BUILD_NUMBER}").push()
                    }
                }
            }
        }

        stage('Update Deployment Manifest') {
            when {
                expression {
                    // Skip if commit message contains [skip ci]
                    return !env.GIT_COMMIT_MESSAGE.contains('[skip ci]')
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    script {
                        sh """
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"

                        git checkout main || git checkout -b main

                        git fetch origin main
                        git reset --hard origin/main

                        sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml

                        git add manifests/deployment.yaml

                        # Commit only if changes exist, with [skip ci] to avoid loop
                        git diff --cached --quiet || git commit -m "Update image tag to ${BUILD_NUMBER} [skip ci]"

                        git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git

                        git push --force-with-lease origin main

                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        """
                    }
                }
            }
        }
    }
}
