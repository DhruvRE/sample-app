pipeline {
    agent any

    parameters {
        string(name: 'SOURCE_BRANCH', defaultValue: 'dbranch', description: 'Branch to build and merge into main')
    }

    environment {
        DOCKER_IMAGE       = "dhruvre/sample-app"
        DOCKER_CREDENTIALS = "dockerhub-credentials-id"
        GIT_CREDENTIALS    = "github-token"
        GIT_REPO           = "https://github.com/DhruvRE/sample-app.git"
        SONAR_HOST_URL     = "http://sonarqube:9000"
        SONAR_PROJECT_KEY  = "jenkins-sonar-app"
        STAGING_NS         = "sample-app-staging"
        PROD_NS            = "sample-app-production"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: "*/${params.SOURCE_BRANCH}"]],
                          userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
            }
        }

        stage('Setup & Install') {
            steps {
                sh '''
                    python3 -m venv myenv
                    . myenv/bin/activate
                    pip install --upgrade pip
                    pip install -r app/requirements.txt
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . myenv/bin/activate
                    PYTHONPATH=$PYTHONPATH:$(pwd) pytest test/unit --maxfail=1 --disable-warnings --cov=app --cov-report xml:app/coverage.xml
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                dir('app') {
                    withSonarQubeEnv('MySonarQube') {
                        script {
                            def scannerHome = tool 'SonarScanner'
                            sh """
                                set -e
                                ${scannerHome}/bin/sonar-scanner \
                                    -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                    -Dsonar.sources=. \
                                    -Dsonar.python.coverage.reportPaths=../coverage.xml \
                                    -Dsonar.host.url=${SONAR_HOST_URL} \
                                    -Dsonar.ex`clusions=venv/**,**/__pycache__/**,**/*.pyc
                            """
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to Quality Gate failure: ${qg.status}"
                        }
                        echo "Quality Gate passed with status: ${qg.status}"
                    }
                }
            }
        }

        stage('Build & Push Staging Image') {
            steps {
                script {
                    env.STAGING_TAG = "${BUILD_NUMBER}-staging"
                    docker.build("${DOCKER_IMAGE}:${STAGING_TAG}", "app")
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}:${STAGING_TAG}").push()
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                script {
                    sh '''
                        export NAMESPACE=${STAGING_NS}
                        export IMAGE_TAG=${STAGING_TAG}
                        export DOCKER_IMAGE=${DOCKER_IMAGE}
                        export REPLICAS=2

                        envsubst < manifests/deployment.yaml | kubectl apply -f -
                        envsubst < manifests/service.yaml | kubectl apply -f -
                        kubectl rollout status deployment/sample-app -n ${NAMESPACE}
                    '''
                }
            }
        }

        stage('Integration Tests') {
            steps {
                sh '''
                    . myenv/bin/activate
                    pytest test/integration --maxfail=1 --disable-warnings
                '''
            }
        }

        stage('Build & Push Production Image') {
            steps {
                script {
                    env.PROD_TAG = "${BUILD_NUMBER}"
                    docker.build("${DOCKER_IMAGE}:${PROD_TAG}", "app")
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}:${PROD_TAG}").push()
                    }
                }
            }
        }

        stage('Deploy to Production') {
            steps {
                script {
                    sh '''
                        export NAMESPACE=${PROD_NS}
                        export IMAGE_TAG=${PROD_TAG}
                        export DOCKER_IMAGE=${DOCKER_IMAGE}
                        export REPLICAS=3

                        envsubst < manifests/deployment.yaml | kubectl apply -f -
                        envsubst < manifests/service.yaml | kubectl apply -f -
                        kubectl rollout status deployment/sample-app -n ${NAMESPACE}
                    '''
                }
            }
        }

        stage('Merge Branch into Main') {
            steps {
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    sh '''
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"

                        git fetch origin ${SOURCE_BRANCH}:${SOURCE_BRANCH}
                        git checkout main || git checkout -b main origin/main
                        git merge --no-ff ${SOURCE_BRANCH} -m "Merge ${SOURCE_BRANCH} into main [skip ci]"

                        sed -i "s|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${PROD_TAG}|" manifests/deployment.yaml
                        git add manifests/deployment.yaml
                        git diff --cached --quiet || git commit -m "Update image tag to ${PROD_TAG} [skip ci]"

                        git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git
                        git push origin main
                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                    '''
                }
            }
        }
    }
}
