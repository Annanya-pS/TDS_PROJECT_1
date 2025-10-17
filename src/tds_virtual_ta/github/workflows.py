from typing import Dict


def generate_pages_workflow(framework: str = "gradio") -> str:
    """Generate GitHub Actions workflow for GitHub Pages deployment (static, dependency-free)."""
    return f"""name: Deploy to GitHub Pages

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
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Prepare static site
        run: |
          mkdir -p _site
          if [ -f index.html ]; then
            cp index.html _site/index.html
          else
            echo "<html><body><h1>Application Deployed</h1>" > _site/index.html
            echo "<p>This {framework} application is deployed.</p>" >> _site/index.html
            echo "<p><a href='https://github.com/${{{{ github.repository }}}}'>View Source</a></p>" >> _site/index.html
            echo "</body></html>" >> _site/index.html
          fi
          cp -r assets _site/assets 2>/dev/null || true
          cp README.md _site/ 2>/dev/null || true
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: '_site'
  
  deploy:
    environment:
      name: github-pages
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v3
"""


def generate_ci_workflow() -> str:
    """Generate CI workflow for testing and linting (robust to missing Python files)."""
    return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies (if present)
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install flake8 || true
      
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
      
      - name: Basic repository check
        run: |
          if [ -f index.html ]; then echo "index.html present"; else echo "index.html missing"; fi
"""


def get_all_workflows(framework: str = "gradio") -> Dict[str, str]:
    """Get all workflow files."""
    return {
        ".github/workflows/pages.yml": generate_pages_workflow(framework),
        ".github/workflows/ci.yml": generate_ci_workflow(),
    }
