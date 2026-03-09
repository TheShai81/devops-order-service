pipeline {
    agent any

    environment {
        IMAGE_NAME = "shaileshbolduc/order-service"
        TAG = "build-${BUILD_NUMBER}"
        KUBECONFIG = "C:\\Users\\srbol\\.kube\\config"
        KUBE_CONTEXT = "devops"
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
                    echo "Image to use: ${IMAGE_NAME}:${TAG}"
                }
            }
        }

        stage('Build') {
            steps {
                bat '''
                python -m venv venv
                call venv\\Scripts\\activate
                pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                call venv\\Scripts\\activate
                pip install pytest
                pytest tests --maxfail=1 --disable-warnings -q
                '''
            }
        }

        stage('Security Scan') {
            steps {
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
                bat """
                docker build -t ${IMAGE_NAME}:${TAG} .
                """
            }
        }

        stage('Container Push') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'main'
                    expression { env.BRANCH_NAME.startsWith('release/') }
                }
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

        stage('Deploy to Dev') {
            when { branch 'develop' }
            steps {
                bat """
                set KUBECONFIG=${KUBECONFIG}
                kubectl config use-context ${KUBE_CONTEXT}
                kubectl set image deployment/order order=${IMAGE_NAME}:${TAG} -n dev
                kubectl rollout status deployment/order -n dev --timeout=120s
                """
            }
        }

        stage('Deploy to Staging') {
            when { expression { env.BRANCH_NAME.startsWith('release/') } }
            steps {
                bat """
                set KUBECONFIG=${KUBECONFIG}
                kubectl config use-context ${KUBE_CONTEXT}
                kubectl set image deployment/order order=${IMAGE_NAME}:${TAG} -n staging
                kubectl rollout status deployment/order -n staging --timeout=120s
                """
            }
        }

        stage('Deploy to Production') {
            when { branch 'main' }
            steps {
                script {
                    input message: "Approve Production Deployment?"
                }
                bat """
                set KUBECONFIG=${KUBECONFIG}
                kubectl config use-context ${KUBE_CONTEXT}
                kubectl set image deployment/order order=${IMAGE_NAME}:${TAG} -n prod
                kubectl rollout status deployment/order -n prod --timeout=120s
                """
            }
        }
    }

    post {
        failure {
            bat """
            set KUBECONFIG=${KUBECONFIG}
            kubectl get deployments -A
            kubectl get pods -A
            kubectl get events -A --sort-by=.metadata.creationTimestamp
            """
        }
    }
}
