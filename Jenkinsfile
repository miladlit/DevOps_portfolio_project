pipeline {
  agent { label 'docker' }
  options { timeout(time: 20, unit: 'MINUTES'); disableConcurrentBuilds() }
  stages {
    stage('Test') { steps { sh 'command -v nginx'; sh 'bash scripts/test.sh' } }
    stage('Container') { steps { sh 'bash scripts/test-container.sh' } }
    stage('Package') {
      steps {
        sh 'python3 scripts/release.py HEAD'
        sh 'cd dist && sha256sum -c *.sha256'
      }
    }
  }
  post {
    success { archiveArtifacts artifacts: 'dist/*.tar.gz,dist/*.sha256', fingerprint: true }
    always { deleteDir() }
  }
}
