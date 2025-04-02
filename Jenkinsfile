pipeline {
  agent any

  environment {
    // Define the Docker image name
    IMAGE_NAME = "mawhaze/ender_bot"
    // Enable Docker BuildKit
    DOCKER_BUILDKIT = 1
  }

  stages {
    stage('Checkout Code') {
      steps {
        checkout scm
      }
    }

    stage('Build Docker Image') {
      steps {
        script {
          // Build the Docker image, no ssh keys required at this time
          sh "docker buildx build --progress=plain -t ${env.IMAGE_NAME}:latest ."
        }
      }
    }

    stage('Docker Login and Push') {
      steps {
        script {
          // Use withCredentials to securely handle DockerHub login
          withCredentials([
            string(credentialsId: 'dockerhub_username', variable: 'DOCKERHUB_USERNAME'),
            string(credentialsId: 'dockerhub_password', variable: 'DOCKERHUB_PASSWORD')
          ]) {
            // Log in to DockerHub
            sh "docker login -u ${env.DOCKERHUB_USERNAME} -p ${env.DOCKERHUB_PASSWORD}"
            // Push the Docker image to DockerHub
            sh "docker push ${env.IMAGE_NAME}:latest"
          }
        }
      }
    }
  }
}