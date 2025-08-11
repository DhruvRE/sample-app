pipeline {
    agent any

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
    }

    triggers {
        // Trigger on both develop and main branches push
        githubPush()
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: "${env.BRANCH_NAME}"]],
                          userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
            }
        }

        stage('Check for skip commit') {
            steps {
                script {
                    def lastCommitMsg = sh(script: "git log -1 --pretty=%B", returnStdout: true).trim()
                    if (lastCommitMsg.contains("[ci skip]")) {
                        echo "Last commit contains [ci skip], skipping build."
                        currentBuild.result = 'SUCCESS'
                        error("Build skipped due to [ci skip] tag in commit message.")
                    }
                }
            }
        }

        stage('Build and Test') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}", "app")
                    // Insert your test commands here if any
                }
            }
        }

        stage('Push Docker Image') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'main'
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

        stage('Merge develop to main') {
            when {
                branch 'develop'
            }
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
                        git merge develop --no-ff -m "Merge develop into main [ci skip]"
                        git push https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git main
                        """
                    }
                }
            }
        }

        stage('Update Deployment Manifest') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    script {
                        sh """
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"
                        git checkout main
                        git fetch origin main
                        git reset --hard origin/main

                        sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml

                        git add manifests/deployment.yaml
                        git diff --cached --quiet || git commit -m "Update image tag to ${BUILD_NUMBER} [ci skip]"

                        git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git
                        git push --force-with-lease origin main
                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        """
                    }
                }
            }
        }

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
