# GitHub To AWS Auto-Deploy (OIDC)

This repo is set to auto-deploy on every push to `main` using GitHub Actions and AWS OIDC.

## What Happens On Push
1. Build site with `npm run build`
2. Upload HTML to S3 with short cache
3. Upload static assets to S3
4. Invalidate CloudFront (`/*`)

## One-Time AWS Setup

### 1) Ensure GitHub OIDC provider exists in IAM
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

If it already exists, AWS returns an error. That is fine.

### 2) Create deploy role for GitHub Actions
```bash
aws iam create-role \
  --role-name github-actions-thelab-oidc \
  --assume-role-policy-document file://github-oidc-trust-policy.json
```

### 3) Attach S3 + CloudFront permissions
```bash
aws iam put-role-policy \
  --role-name github-actions-thelab-oidc \
  --policy-name GitHubActionsTheLabDeploy \
  --policy-document file://github-iam-policy.json
```

### 4) Add one GitHub secret
Repository:
`https://github.com/iamMichaelSmith/The-Lab-Barbershop-Website/settings/secrets/actions`

Create:
- `AWS_ROLE_TO_ASSUME` = `arn:aws:iam::309014076408:role/github-actions-thelab-oidc`

## Trigger Deploy
```bash
git add .
git commit -m "Enable secure GitHub->AWS auto deploy"
git push origin main
```

## Verify
- GitHub Actions runs:
  `https://github.com/iamMichaelSmith/The-Lab-Barbershop-Website/actions`
- Site updates via CloudFront after the workflow finishes.

## Security Note
Do not use long-lived IAM access keys for this pipeline. OIDC is keyless and safer.
