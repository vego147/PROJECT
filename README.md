# AI Marketing Content Engine

An internship prototype for researching a topic, generating an article
and social-media copy, creating an editorial image, and saving generated
posts for later review.

> **Prototype status:** This project is not production-ready. Generated
> content must be reviewed before publishing. Research results and
> AI-generated verification are not proof that every claim is true.

## Features

-   FastAPI backend with `/api/health`, `/api/generate`, and saved-post
    endpoints.
-   Research service that gathers source material for a requested topic.
-   Groq-powered content generation for an article, social title,
    caption, hashtags, call to action, and image prompt.
-   Cloudflare Workers AI image generation (configured for FLUX.1
    Schnell in the current implementation).
-   Local template fallback when LLM generation fails. Fallback output
    should be clearly labelled and reviewed.
-   SQLAlchemy persistence for generated posts.
-   Optional claim-verification layer, if `app/services/verification.py`
    has been added and connected to the API.
-   React frontend, typically served by Vite on port `5173`.

## Project structure

The exact filenames can differ by checkout. The backend imports shown in
the current implementation include:

``` text
project/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       └── services/
│           ├── research.py
│           ├── generation.py
│           ├── images.py
│           └── verification.py   # optional, if added
├── frontend/                     # React/Vite frontend, if present
├── .env                          # create locally; do not commit
└── README.md
```

Use the actual folder names in your downloaded project if they differ.

## Requirements

-   Python 3.10+ recommended; use the version supported by the project's
    dependencies.
-   Node.js and npm, if running the React frontend.
-   API credentials for the external services you enable.
-   Internet access for external research, Groq, and Cloudflare calls.

## 1. Get the project ready

Open a terminal in the project root (the folder containing the backend
and frontend directories).

Create and activate a Python virtual environment:

### Linux

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

``` powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
```

Install the backend dependencies using the project's requirements file,
if provided:

``` bash
pip install -r backend/requirements.txt
```

If the requirements file is located elsewhere, run the command from the
directory containing that file. If the project uses `pyproject.toml`
instead, follow that file's installation instructions.

## 2. Configure environment variables

Create a `.env` file in the location read by `app/config.py`. Do not
paste API tokens into source code or commit `.env` to Git.

The following are common variables for this project's integrations.
**Check `backend/app/config.py` and `backend/app/services/images.py` for
the exact variable names expected by your current checkout**; rename
these examples if the code uses different names.

``` dotenv
# LLM content generation
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_supported_groq_model

# Research provider (if the research service uses Tavily)
TAVILY_API_KEY=your_tavily_api_key

# Cloudflare Workers AI image generation
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# Database
# Use the format expected by app/database.py.
# For SQLite, the project may configure a local database automatically.
DATABASE_URL=sqlite:///./content_engine.db
```

Notes:

-   Obtain credentials from the official provider dashboards.
-   Use a model that is currently available to your Groq account.
-   A configured API key does not guarantee that a request will succeed.
    Check model availability, quota, network connectivity, and provider
    status if calls fail.
-   The example SQLite URL is only appropriate if the project's
    SQLAlchemy configuration supports it. Keep the project's existing
    database configuration if it differs.
-   If a provider is not configured, the application may use a fallback
    or mark the relevant stage as failed, depending on the
    implementation.

## 3. Start the backend

From the project root, activate the virtual environment and run Uvicorn.

For a package layout where `app` is inside `backend/`:

``` bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `uvicorn` is not installed, install the project's requirements or
run:

``` bash
pip install fastapi uvicorn
```

Keep this terminal open while using the application.

### Check the backend

Open these URLs in a browser:

-   Health check: `http://127.0.0.1:8000/api/health`
-   Interactive API documentation: `http://127.0.0.1:8000/docs`

The health endpoint should return a small JSON response indicating that
the service is running. This checks that FastAPI is alive; it does
**not** prove that Groq, research, image generation, or the database is
working.

## 4. Start the frontend

Open a second terminal. If the frontend directory contains
`package.json`:

``` bash
cd frontend
npm install
npm run dev
```

Vite usually serves the app at:

``` text
http://localhost:5173
```

The backend CORS configuration currently allows `http://localhost:5173`
and `http://127.0.0.1:5173`. If Vite uses another port, update the
allowed origins in `backend/app/main.py` or run Vite on an allowed
origin.

If the frontend is in a different directory, run the commands in the
directory containing its `package.json`.

## 5. Generate a post

1.  Open the frontend in your browser.
2.  Enter a topic of at least three characters.
3.  Select the desired platform and tone.
4.  Submit the generation request.
5.  Review the article, caption, hashtags, image, sources, stages, and
    warnings.
6.  Verify factual claims against the original sources before using the
    content.

The main endpoint is:

``` http
POST /api/generate
Content-Type: application/json
```

The request schema is defined by `GenerateRequest` in `app/schemas.py`.
Check that file for the exact required fields and accepted values for
`platform` and `tone`.

Other endpoints in the current backend:

``` http
GET /api/health
GET /api/posts?limit=8
GET /api/posts/{post_id}
```

The post list endpoint limits the requested number of records to a
maximum of 100.

## 6. Verification and fallback behavior

If the verification service has been added and connected:

-   Treat `supported` as supported by the supplied source text, not as a
    guarantee of truth.
-   Treat `contradicted` and `insufficient_evidence` as reasons to
    review the article.
-   If verification fails or cannot run, do not mark the article as
    verified.
-   Block automatic publishing when material claims are contradicted or
    lack adequate evidence.

The generation fallback is a recovery mechanism, not a substitute for
LLM generation. Clearly label fallback content in the UI and do not
publish it automatically. A successful HTTP response alone is not proof
of content quality.

## 7. Troubleshooting

### `Groq is not configured` or the content uses the fallback template

-   Confirm the API key is present in the environment loaded by the
    backend.
-   Confirm the variable name matches `app/config.py`.
-   Restart Uvicorn after changing `.env`.
-   Confirm the selected model is available to your account.
-   Inspect the backend terminal for the original exception, including
    authentication, rate-limit, timeout, and invalid-response errors.

### `LLM response missing required fields` or an article is too short

-   Check the prompt and response parser in
    `app/services/generation.py`.
-   Validate all required fields and enforce the article word-count
    limit.
-   Retry incomplete responses with a correction prompt.
-   If retries fail, mark the output as fallback or return an explicit
    error; never label template content as LLM-generated.

### Cloudflare image generation fails

-   Confirm the account ID, API token, and environment variable names.
-   Check that the token has permission to use Workers AI and that the
    account has available usage or balance.
-   Check network/DNS connectivity and the exact model identifier
    configured in `app/services/images.py`.
-   Review the backend log for the provider's HTTP status and response
    body.
-   If a placeholder image is used, display a warning and require a real
    image before publishing.

### Frontend cannot call the API

-   Confirm the backend is running on port `8000`.
-   Confirm the frontend is using the correct API base URL.
-   Check browser developer tools for CORS errors and failed requests.
-   Ensure the frontend origin matches the backend CORS allowlist.

### Database or saved-post errors

-   Inspect `app/database.py` for the configured database URL.
-   Confirm the process can write to the database location.
-   `Base.metadata.create_all()` creates missing tables but does not
    migrate existing tables when model columns change. Use a migration
    or carefully recreate a disposable development database after
    backing up any data you need.

### Dependency or import errors

-   Activate the intended virtual environment.
-   Install the dependencies from the project's own requirements or
    project configuration file.
-   Run Uvicorn from the directory that makes the `app` package
    importable.

## 8. Security and publishing checklist

Before using this beyond a local demonstration:

-   Keep API keys in environment variables and out of Git.
-   Add `.env`, virtual environments, generated databases, and build
    artifacts to `.gitignore`.
-   Validate request data and handle provider errors without exposing
    secrets.
-   Add authentication and rate limiting before exposing the API
    publicly.
-   Persist verification results and review status if posts are saved
    for later use.
-   Require human approval before publication.
-   Verify source URLs, publication dates, quotations, figures, and
    other material claims.
-   Do not describe a draft as verified unless the evidence and
    verification process justify that wording.

## Development status

This README describes the current prototype flow and the endpoints
visible in the supplied backend code. Some configuration names, frontend
paths, and dependency-file locations must be checked against the actual
repository before the commands can be considered exact.
