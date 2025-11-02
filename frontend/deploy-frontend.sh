#!/usr/bin/env bash
set -euo pipefail

# ===============================================================
# Script : deploy_frontend_s3_cf.sh
# Objectif : Builder et déployer une app Vite/React
#            sur S3 + CloudFront (HTTPS via Route 53)
# ===============================================================

# --- Charger le fichier .env ---
if [ -f .env ]; then
  echo "🔄 Chargement des variables depuis .env..."
  set -a
  source .env
  set +a
else
  echo "❌ Aucun fichier .env trouvé à la racine du projet."
  exit 1
fi

# --- Vérification des variables requises ---
REQUIRED_VARS=(
  "AWS_REGION"
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "AWS_S3_BUCKET_NAME"
  "AWS_CLOUDFRONT_DISTRIBUTION_ID"
)

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "❌ Erreur : la variable $var n'est pas définie."
    exit 1
  fi
done

echo "✅ Variables d'environnement chargées avec succès."

# --- Vérification des outils ---
for cmd in node npm aws; do
  if ! command -v $cmd &>/dev/null; then
    echo "❌ L'outil '$cmd' est requis mais non trouvé dans le PATH."
    exit 1
  fi
done
echo "✅ Outils nécessaires disponibles."

# --- Authentification AWS ---
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_REGION
echo "🔐 Vérification des identifiants AWS..."
aws sts get-caller-identity >/dev/null || { echo "❌ Authentification AWS échouée."; exit 1; }
echo "✅ Authentification AWS réussie."

# --- Installation des dépendances ---
echo "📦 Installation des dépendances..."
npm ci || npm install

# --- Build du projet ---
echo "⚙️  Build du projet Vite..."
npm run build

# --- Déploiement frontend sur S3 ---
echo "🚀 Déploiement du frontend sur S3..."
aws s3 sync dist/ "s3://$AWS_S3_BUCKET_NAME" --delete

# --- Invalidation CloudFront ---
echo "🧹 Invalidation du cache CloudFront..."
aws cloudfront create-invalidation \
  --distribution-id "$AWS_CLOUDFRONT_DISTRIBUTION_ID" \
  --paths "/*"

echo "🎉 Déploiement terminé !"
echo "🌍 Ton app est disponible sur : https://mlops.kassatech.org"