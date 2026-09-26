# ReelsPulse - Instagram Reels Trending & Growth Velocity Engine

A compliance-first analytics and discovery dashboard tracking trending Instagram Reels across 4 key technology categories.

Designed as a **single, unified full-stack application** (FastAPI backend + Vite React frontend) with native support for **Neon Serverless PostgreSQL** and ready for one-click single-app deployment on **Render** or **Vercel**.

---

## 🌟 4 Content Categories

1. **💻 Niche (Latest in Tech)**:
   - What's new in the tech field: breakthrough websites, secret web apps, Android/iOS apps, new gadgets, and viral tech reels gaining huge popularity on Instagram.
2. **🤖 AI (Crazy AI Tools & Prompts)**:
   - Mind-blowing new AI tools and websites, crazy photo-to-prompt tricks (e.g. upload a selfie + secret prompt for hyperrealistic outputs), talking video avatars, and model releases.
3. **🌐 Other (Tech-Adjacent & Viral Trends)**:
   - Content loosely related to tech: prompt lifestyle tricks, developer humor, tech satire, and creative media trends gaining explosive Instagram virality.
4. **⛓️ Blockchain (Web3 & Fresher Jobs)**:
   - New developments in Web3, Solidity smart contracts, DeFi architectures, ZK-rollups, and roadmaps/interview questions/portfolio projects to help freshers land a high-paying job in blockchain.

---

## 🗄️ Neon Serverless PostgreSQL Setup

The database layer automatically detects your Neon connection string, normalizes `postgres://` to `postgresql://`, and configures connection pooling (`pool_pre_ping=True`, `pool_recycle=300`) to prevent dropped serverless connections.

### How to connect Neon PostgreSQL:
1. Create a database on [Neon Console](https://console.neon.tech).
2. Copy your connection string from the dashboard.
3. Set the environment variable in `.env` or your hosting platform:
```bash
DATABASE_URL=postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
```
*(If `DATABASE_URL` is omitted, the app automatically falls back to local SQLite `roshan.db` for instant local testing!)*

---

## 🚀 Single-App Deployment Analysis: Render vs. Vercel

### Recommendation: **Render** ⭐

| Criteria | **Render (RECOMMENDED)** | **Vercel** |
|---|---|---|
| **Architecture** | **Native Single Unified Web Service** (FastAPI serves both APIs and pre-built Vite React static assets) | **Serverless Function Split** (Requires `@vercel/python` lambdas + route rewrites) |
| **Execution Limits** | **No timeout limit** on standard processes (data syncs, velocity calculations, and database seeding run uninterrupted) | **15s execution timeout** on free tier; background syncs get killed |
| **Neon Connection Pool** | Persistent connection pool keeps connections warm and stable | Ephemeral serverless lambdas create new connections on every cold start |
| **Simplicity** | **1-Click**: 1 build command, 1 start command | Requires complex `vercel.json` routing rules |

---

### Step-by-Step Deployment on Render (Single App)

1. Push your repository to GitHub / GitLab.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New → Web Service**.
3. Select your repository.
4. Configure the settings:
   - **Name**: `reelspulse`
   - **Environment**: `Python`
   - **Build Command**: `./build.sh` (or `npm run build --prefix frontend && pip install -r requirements.txt && PYTHONPATH=. python3 backend/app/seed.py`)
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string (`postgresql://...sslmode=require`)
   - `PYTHON_VERSION`: `3.13.0`
6. Click **Deploy Web Service**!

Render will build the Vite frontend, install Python dependencies, seed the Neon PostgreSQL database with 420 reels across all 4 categories, and launch the single unified application on a free HTTPS URL!

---

### Step-by-Step Deployment on Vercel (Alternative)

If you prefer Vercel, the repository already includes [`vercel.json`](file:///home/kali/UserData/G/projects/roshan/vercel.json):
1. Install Vercel CLI (`npm i -g vercel`) or import the repo on [vercel.com](https://vercel.com).
2. Set Environment Variable:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
3. Deploy:
```bash
vercel --prod
```

---

## 🧪 Local Quick Start

Run the all-in-one local runner:
```bash
./start.sh
```

- **Dashboard UI**: [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
