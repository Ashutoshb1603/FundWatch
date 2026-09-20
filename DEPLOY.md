# Deploying FundWatch to AWS (App Runner + Amplify)

Backend = the tested FastAPI app on App Runner (uses Groq for the LLM).
Frontend = Next.js on Amplify Hosting. Scans are held in memory, so keep the
backend at a **single instance** (min 1, max 1).

## 0. Push the code
Make sure `backend/apprunner.yaml` and the latest changes are pushed to GitHub
(`git add -A && git commit && git push`). Never commit `backend/.env`.

## 1. Backend on App Runner (console)
1. AWS Console -> **App Runner** -> Create service.
2. Source: **Source code repository** -> connect GitHub -> pick the FundWatch repo, branch `main`.
   **Source directory: `backend`**. Deployment: automatic.
3. Configuration: **Use a configuration file** (reads `backend/apprunner.yaml`).
4. Service settings: CPU 1 vCPU, **Memory 2 GB** (PDF parsing), then
   **Environment variables** -> add `GROQ_API_KEY` (choose "Secret" type or plain
   for a hackathon). Region: any (e.g. ap-south-1).
5. Auto scaling: create a config with **min 1, max 1**.
6. Health check: HTTP, path `/api/health`.
7. Create. When Running, copy the **default domain**, e.g. `https://abc123.ap-south-1.awsapprunner.com`.
8. Verify: open `<domain>/api/health` -> `{"status":"ok"}`; `<domain>/docs` works.

## 2. Frontend on Amplify Hosting (console)
1. AWS Console -> **Amplify** -> Create new app -> GitHub -> same repo/branch.
2. Check "My app is a monorepo" and set the app root to `frontend`.
3. Environment variables (must be set before the build):
   - `NEXT_PUBLIC_API_BASE_URL` = the App Runner URL from step 1 (no trailing slash)
   - leave `NEXT_PUBLIC_API_MODE` **unset** (only `aws` selects the unused Lambda protocol)
4. Deploy. Amplify detects Next.js automatically.
5. Open the Amplify URL, click "Use sample", Compare factsheets.

## 3. Checks / gotchas
- Blank result or network error: confirm `NEXT_PUBLIC_API_BASE_URL` starts with `https://` and was set
  before the build (redeploy after changing it). CORS already allows all origins.
- Groq free tier is ~8k tokens/min; avoid rapid chat messages during the demo.
- First request after idle can be slow; open the app once before presenting.
- Redeploying the backend clears stored scans (in-memory), so run a fresh analysis afterwards.
- To stop charges after the hackathon: delete the App Runner service and the Amplify app.
