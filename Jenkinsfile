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
                          branches: [[name: 'refs/heads/main']],
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
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"
                        git fetch origin main
                        git checkout main
                        git reset --hard origin/main

                        sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml

                        # Check last commit author
                        LAST_COMMIT_AUTHOR=\$(git log -1 --pretty=format:'%an')
                        echo "Last commit author: \$LAST_COMMIT_AUTHOR"

                        if [ "\$LAST_COMMIT_AUTHOR" != "Jenkins CI" ]; then
                        git add manifests/deployment.yaml
                        git diff --cached --quiet || git commit -m "Update image tag to ${BUILD_NUMBER} [ci skip]"
                        git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git
                        git push origin main
                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        else
                        echo "Last commit by Jenkins CI, skipping push to avoid loop."
                        fi
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


// pipeline {
//     agent any

//     environment {
//         DOCKER_IMAGE       = "dhruvre/sample-app"
//         DOCKER_CREDENTIALS = "dockerhub-credentials-id"
//         GIT_CREDENTIALS    = "github-token"
//         GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
//     }

//     stages {
//         stage('Checkout Code') {
//             steps {
//                 checkout([$class: 'GitSCM',
//                           branches: [[name: 'refs/heads/main']],
//                           userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
//             }
//         }

//         stage('Check for skip commit') {
//             steps {
//                 script {
//                     def lastCommitMsg = sh(script: "git log -1 --pretty=%B", returnStdout: true).trim()
//                     if (lastCommitMsg.contains("[ci skip]")) {
//                         echo "Last commit contains [ci skip], skipping build."
//                         currentBuild.result = 'SUCCESS'
//                         // Setting a flag to skip next stages
//                         env.SKIP_BUILD = "true"
//                     }
//                 }
//             }
//         }

//         stage('Build Docker Image') {
//             when {
//                 expression { env.SKIP_BUILD != "true" }
//             }
//             steps {
//                 script {
//                     docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}", "app")
//                 }
//             }
//         }

//         stage('Push Docker Image') {
//             when {
//                 expression { env.SKIP_BUILD != "true" }
//             }
//             steps {
//                 script {
//                     docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS) {
//                         docker.image("${DOCKER_IMAGE}:${env.BUILD_NUMBER}").push()
//                     }
//                 }
//             }
//         }

//         stage('Update Deployment Manifest') {
//             when {
//                 expression { env.SKIP_BUILD != "true" }
//             }
//             steps {
//                 withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
//                                                   usernameVariable: 'GIT_USER',
//                                                   passwordVariable: 'GIT_TOKEN')]) {
//                     script {
//                         sh """
//                         git config user.email "jenkins@local"
//                         git config user.name "Jenkins CI"
//                         git fetch origin main
//                         git checkout main
//                         git reset --hard origin/main

//                         sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml

//                         git add manifests/deployment.yaml
//                         git diff --cached --quiet || git commit -m "Update image tag to ${BUILD_NUMBER} [ci skip]"

//                         git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git
//                         git push origin main
//                         git remote set-url origin https://github.com/DhruvRE/sample-app.git
//                         """
//                     }
//                 }
//             }
//         }

//         stage('Cleanup Old Docker Images') {
//             when {
//                 expression { env.SKIP_BUILD != "true" }
//             }
//             steps {
//                 script {
//                     sh '''
//                     echo "Cleaning up old docker images for ${DOCKER_IMAGE}..."
//                     docker images --format "{{.Repository}} {{.Tag}} {{.ID}} {{.CreatedAt}}" | \
//                     grep "^${DOCKER_IMAGE} " | \
//                     sort -k4 -r | \
//                     awk 'NR>5 { print $3 }' | \
//                     xargs -r docker rmi || true
//                     '''
//                 }
//             }
//         }
//     }
// }
