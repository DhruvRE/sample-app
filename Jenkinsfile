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
        SONAR_TOKEN        = "sonar-token-id"
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
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pytest --maxfail=1 --disable-warnings -q --cov=. --cov-report xml:coverage.xml
                    '''
                }
            }
        }
        stage('SonarQube Analysis') {
            steps {
                dir('app') {
                    // Ensure SONAR_TOKEN is read from Jenkins credentials securely
                    withCredentials([string(credentialsId: 'sonar-token-id', variable: 'SONAR_TOKEN')]) {
                        // withSonarQubeEnv injects SONAR_HOST_URL and related env vars if you configured "MySonarQube" in Manage Jenkins
                        withSonarQubeEnv('MySonarQube') {
                            script {
                                // Use official SonarScanner Docker image to run the scanner reliably
                                docker.image('sonarsource/sonar-scanner-cli:latest').inside('--user root') {
                                    sh '''
                                        # debug output - helpful if something fails
                                        echo "Running sonar-scanner in $(pwd)"
                                        echo "SONAR_HOST_URL=$SONAR_HOST_URL"
                                        echo "Using workspace: $WORKSPACE"

                                        sonar-scanner \
                                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                        -Dsonar.sources=. \
                                        -Dsonar.host.url=${SONAR_HOST_URL} \
                                        -Dsonar.login=${SONAR_TOKEN} \
                                        -Dsonar.python.coverage.reportPaths=coverage.xml -X
                                    '''
                                }
                            }
                        }
                    }
                }
            }
        }

        stage('Quality Gate Check') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        // Wait for SonarQube analysis to finish and fetch the quality gate status
                        def qg = waitForQualityGate()
                        echo "Quality Gate status: ${qg.status}"
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to Quality Gate failure: ${qg.status}"
                        }

                        // Optionally check coverage metric via Sonar API (still uses SONAR_TOKEN)
                        withCredentials([string(credentialsId: 'sonar-token-id', variable: 'SONAR_TOKEN')]) {
                            def coverageJson = sh(
                                script: """curl -s -u ${SONAR_TOKEN}: ${SONAR_HOST_URL}/api/measures/component?component=${SONAR_PROJECT_KEY}&metricKeys=coverage""",
                                returnStdout: true
                            ).trim()
                            echo "Sonar measures: ${coverageJson}"
                            def coverage = sh(
                                script: "echo '${coverageJson}' | jq -r '.component.measures[0].value'",
                                returnStdout: true
                            ).trim()
                            echo "Coverage from SonarQube: ${coverage}%"
                            if (coverage != '' && coverage.toFloat() < 80) {
                                error "Pipeline failed: Coverage is ${coverage}%, required >= 80%"
                            }
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
                        git config user.email "jenkins@local"
                        git config user.name "Jenkins CI"

                        git fetch origin ${SOURCE_BRANCH}:${SOURCE_BRANCH}
                        git checkout main || git checkout -b main origin/main
                        git merge --no-ff ${SOURCE_BRANCH} -m "Merge ${SOURCE_BRANCH} into main [skip ci]"

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
