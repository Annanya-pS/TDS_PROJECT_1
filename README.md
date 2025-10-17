---
title: TDS Virtual TA
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# TDS Virtual TA - LLM Code Deployment Service

Automated code generation and deployment service for IIT Madras TDS project.

## Overview

This service receives task requests, generates static web applications using LLMs, creates GitHub repositories, and deploys to GitHub Pages automatically.

## API Endpoint

**POST** `/api-endpoint`

Request format:
```json
{
  "email": "student@example.com",
  "secret": "your-secret",
  "task": "app-name-abc123",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Create a calculator app",
  "checks": ["Has input fields"],
  "evaluation_url": "https://eval.example.com/notify",
  "attachments": []
}
```

## Environment Variables

Configure via HuggingFace CLI:
- `SERVICE_SECRET` - Authentication secret
- `GITHUB_TOKEN` - GitHub PAT
- `GITHUB_USERNAME` - Your GitHub username
- `AIPIPE_API_KEY` - AIPipe.org API key
- `AIPIPE_BASE_URL` - AIPipe API URL
- `AIPIPE_MODEL` - Model to use
- `HF_TOKEN` - HuggingFace token
- `LOG_LEVEL` - Logging level

## Testing
```bash
curl https://annanyaps-tds-project-1.hf.space/health
```

## License

MIT License
