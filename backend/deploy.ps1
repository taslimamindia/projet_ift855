Write-Host "🚀 Starting deployment to Google Cloud Run (PowerShell)..." -ForegroundColor Green

# In PowerShell, the backtick (`) is used for line continuation
gcloud run deploy project-ift855-backend `
    --source . `
    --project "project-ift855" `
    --region us-east1 `
    --allow-unauthenticated `
    --memory=2Gi `
    --set-secrets="ENV=ENV:latest" `
    --set-secrets="FIREWORKS_API_KEY=FIREWORKS_API_KEY:latest" `
    --set-secrets="MODEL_EMBEDDINGS_NAME=MODEL_EMBEDDINGS_NAME:latest" `
    --set-secrets="MODEL_LLM_NAME=MODEL_LLM_NAME:latest" `
    --set-secrets="DEPLOYMENT_TYPE=DEPLOYMENT_TYPE:latest" `
    --set-secrets="AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID:latest" `
    --set-secrets="AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY:latest" `
    --set-secrets="AWS_REGION=AWS_REGION:latest" `
    --set-secrets="AWS_S3_BUCKET_NAME_BACKEND=AWS_S3_BUCKET_NAME_BACKEND:latest" `
    --set-secrets="BASE_PREFIX=BASE_PREFIX:latest" `
    --set-secrets="CLEARML_WEB_HOST=CLEARML_WEB_HOST:latest" `
    --set-secrets="CLEARML_API_HOST=CLEARML_API_HOST:latest" `
    --set-secrets="CLEARML_FILES_HOST=CLEARML_FILES_HOST:latest" `
    --set-secrets="CLEARML_API_ACCESS_KEY=CLEARML_API_ACCESS_KEY:latest" `
    --set-secrets="CLEARML_API_SECRET_KEY=CLEARML_API_SECRET_KEY:latest"

if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment finished!" -ForegroundColor Green
} else {
        Write-Host "❌ Deployment failed." -ForegroundColor Red
}