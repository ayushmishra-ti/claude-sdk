#!/bin/bash
# Deploy new_exp (MCQ skill service) to Cloud Run
# Target: https://inceptagentic-skill-mcq-413562643011.us-central1.run.app/generate
# Run from repo root: bash new_exp/deploy.sh

set -e

# Target URL: https://inceptagentic-skill-mcq-413562643011.us-central1.run.app
# Project number 413562643011 => project ID below (gcloud requires PROJECT_ID not number)
PROJECT_ID="eternal-aspect-485115-e3"
REGION="us-central1"
SERVICE_NAME="inceptagentic-skill-mcq"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/ccapi-repo/${SERVICE_NAME}:latest"

# Run from repo root (agent_sdk_v2) so Docker context has src/ and new_exp/
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=============================================="
echo "Deploying new_exp (MCQ skill service)"
echo "=============================================="
echo ""
echo "Service: ${SERVICE_NAME}"
echo "Region:  ${REGION}"
echo "URL:     https://inceptagentic-skill-mcq-413562643011.us-central1.run.app"
echo ""
echo "Endpoints:"
echo "  GET  /             - Health check"
echo "  POST /generate     - Generate ELA questions (new_exp skills)"
echo ""

echo "Building Docker image (Dockerfile.new_exp)..."
gcloud builds submit . \
  --config cloudbuild-new_exp.yaml \
  --substitutions=_IMAGE_NAME="${IMAGE_NAME}" \
  --project "${PROJECT_ID}"

echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300 \
  --set-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest \
  --project "${PROJECT_ID}"

echo ""
echo "=============================================="
echo "Deployment complete!"
echo "=============================================="
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test:"
echo "  curl ${SERVICE_URL}/"
echo "  curl -X POST ${SERVICE_URL}/generate -H 'Content-Type: application/json' -d '{...}'"
