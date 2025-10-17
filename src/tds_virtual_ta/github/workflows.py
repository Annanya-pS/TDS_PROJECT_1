"""
src/tds_virtual_ta/github/workflows.py
FIXED - Correct workflows for static HTML sites
"""

from typing import Dict


def generate_pages_workflow() -> str:
    """Generate GitHub Actions workflow for GitHub Pages deployment (static HTML)."""
    return """name: Deploy Static Site to GitHub Pages

on:
  push:
    branches: [ main ]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
"""


def generate_ci_workflow() -> str:
    """Generate CI workflow for basic validation."""
    return """name: CI Validation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Validate HTML
        run: |
          if [ ! -f index.html ]; then
            echo "ERROR: index.html not found!"
            exit 1
          fi
          echo "✓ index.html exists"
      
      - name: Validate README
        run: |
          if [ ! -f README.md ]; then
            echo "ERROR: README.md not found!"
            exit 1
          fi
          echo "✓ README.md exists"
      
      - name: Validate LICENSE
        run: |
          if [ ! -f LICENSE ]; then
            echo "ERROR: LICENSE not found!"
            exit 1
          fi
          if ! grep -q "MIT License" LICENSE; then
            echo "ERROR: LICENSE is not MIT!"
            exit 1
          fi
          echo "✓ LICENSE is MIT"
      
      - name: Check HTML structure
        run: |
          if ! grep -q "<!DOCTYPE html>" index.html; then
            echo "WARNING: Missing DOCTYPE declaration"
          fi
          if ! grep -q "<html" index.html; then
            echo "ERROR: Invalid HTML structure"
            exit 1
          fi
          echo "✓ HTML structure valid"
      
      - name: Check Bootstrap CDN
        run: |
          if grep -q "bootstrap" index.html; then
            echo "✓ Bootstrap detected"
          else
            echo "WARNING: Bootstrap not found (may not be required)"
          fi
      
      - name: Summary
        run: |
          echo "========================================"
          echo "Repository validation completed"
          echo "========================================"
          echo "Files checked:"
          ls -lh index.html README.md LICENSE
          echo ""
          echo "HTML file size:"
          wc -c index.html | awk '{print $1 " bytes"}'
"""


def get_all_workflows() -> Dict[str, str]:
    """Get all workflow files for static site deployment."""
    return {
        ".github/workflows/pages.yml": generate_pages_workflow(),
        ".github/workflows/ci.yml": generate_ci_workflow(),
    }
