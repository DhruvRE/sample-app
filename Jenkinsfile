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
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: "*/${params.SOURCE_BRANCH}"]],
                          userRemoteConfigs: [[url: env.GIT_REPO, credentialsId: env.GIT_CREDENTIALS]]])
            }
        }

        stage('Run Tests') {
            steps {
                dir('app') {
                    sh '''
                        set -e
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        # Run tests with coverage, output to coverage.xml in app folder
                        pytest --maxfail=1 --disable-warnings -q --cov=./ --cov-report xml:coverage.xml
                    '''
                }
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
                                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                                    -Dsonar.host.url=${SONAR_HOST_URL} \
                                    -Dsonar.exclusions=venv/**,**/__pycache__/**,**/*.pyc
                            """
                        }
                    }
                }
            }
        }

        stage('Quality Gate Check') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to Quality Gate failure: ${qg.status}"
                        }

                        // Extract coverage from quality gate conditions
                        def coverageMetric = qg.conditions.find { it.metricKey == 'coverage' }
                        if (coverageMetric) {
                            def coverage = coverageMetric.value.toFloat()
                            echo "Coverage from SonarQube: ${coverage}%"
                            if (coverage < 80) {
                                error "Pipeline failed: Coverage is ${coverage}%, required >= 80%"
                            }
                        } else {
                            echo "Coverage metric not found in Quality Gate."
                        }
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

        stage('Merge branch into main') {
            steps {
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS,
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    script {
                        sh """
                        set -e
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"

                        git fetch origin ${SOURCE_BRANCH}:${SOURCE_BRANCH}
                        git checkout main || git checkout -b main origin/main
                        git merge --no-ff ${SOURCE_BRANCH} -m "Merge ${SOURCE_BRANCH} into main [skip ci]"

                        # Update deployment image tag
                        sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${BUILD_NUMBER}|' manifests/deployment.yaml
                        git add manifests/deployment.yaml
                        git diff --cached --quiet || git commit -m "Update image tag to ${BUILD_NUMBER} [skip ci]"

                        git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/DhruvRE/sample-app.git
                        git push origin main
                        git remote set-url origin https://github.com/DhruvRE/sample-app.git
                        """
                    }
                }
            }
        }
    }
}
