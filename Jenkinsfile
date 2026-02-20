pipeline {
    agent any

    environment {
        IMAGE_NAME = "shaileshbolduc/frontend-service"
        TAG = "build-${BUILD_NUMBER}"
    }

    triggers {
        githubPush()
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Determine Environment') {
            steps {
                script {
                    if (env.CHANGE_ID) {
                        TARGET_ENV = "build"
                    } else if (env.BRANCH_NAME == "develop") {
                        TARGET_ENV = "dev"
                    } else if (env.BRANCH_NAME.startsWith("release/")) {
                        TARGET_ENV = "staging"
                    } else if (env.BRANCH_NAME == "main") {
                        TARGET_ENV = "prod"
                    } else {
                        TARGET_ENV = "build"
                    }
                    echo "Target Environment: ${TARGET_ENV}"
                }
            }
        }

        stage('Build') {
            steps {
                echo 'Setting up Python Environment'

                bat '''
                python -m venv venv
                call venv\\Scripts\\activate
                pip install -r requirements.txt
                '''
            }
        }


        stage('Test') {
            steps {
                echo 'Running Tests'

                bat '''
                call venv\\Scripts\\activate
                pip install pytest
                pytest tests --maxfail=1 --disable-warnings -q
                '''
            }
        }


        stage('Security Scan') {
            steps {
                echo 'Running Fast Security Scan'
                bat """
                if not exist "%CD%\\trivy-cache\\db" docker run --rm -v "%CD%\\trivy-cache:/root/.cache" aquasec/trivy:latest image alpine:3.19 >nul

                docker run --rm ^
                -v "%CD%:/app" ^
                -v "%CD%/trivy-cache:/root/.cache" ^
                aquasec/trivy:latest ^
                fs ^
                --scanners vuln ^
                --skip-db-update ^
                --no-progress ^
                --severity HIGH,CRITICAL ^
                --skip-dirs /app/venv ^
                --skip-dirs /app/.git ^
                /app
                """
            }
        }


        stage('Container Build') {
            steps {
                echo 'Building Docker Image'

                bat """
                docker build -t ${IMAGE_NAME}:${TAG} .
                """
            }
        }

        stage('Deploy to Dev') {
            when { branch 'develop' }
            steps {
                echo "Deploying ${IMAGE_NAME}:${TAG} to Dev environment"
                echo "Will implement in phases 4, 5, and 6."
            }
        }

        stage('Deploy to Staging') {
            when { expression { env.BRANCH_NAME.startsWith('release') } }
            steps {
                echo "Deploying ${IMAGE_NAME}:${TAG} to Staging environment"
                echo "Will implement in phases 4, 5, and 6."
            }
        }

        stage('Container Push') {
            when {
                branch 'release'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat """
                    echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin
                    docker push ${IMAGE_NAME}:${TAG}
                    """
                }
            }
        }

        stage('Deploy to Production') {
            when { branch 'main' }
            steps {
                script {
                    if (TARGET_ENV == "prod") {
                        input message: "Approve Production Deployment?"
                    }

                    echo "Deploying ${IMAGE_NAME}:${TAG} to Production environment"
                    echo "Will implement in phases 4, 5, and 6."
                }
            }
        }
    }
}
