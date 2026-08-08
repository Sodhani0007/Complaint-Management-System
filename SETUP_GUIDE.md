# Setup Guide: From Zero to Running

Two paths below — **Path A (Docker)** is simpler and recommended. **Path B** is for if you can't
or don't want to install Docker. Pick one, follow it top to bottom.

---

## Path A — Docker (recommended)

### Step 1: Install Docker Desktop

Go to https://www.docker.com/products/docker-desktop/ and download the installer for your OS
(Windows, Mac, or Linux).

- **Windows**: run the installer. It may ask to enable WSL2 (Windows Subsystem for Linux) — say
  yes and let it install/restart if prompted. This is normal.
- **Mac**: drag Docker to Applications, open it once to finish setup.
- **Linux**: follow the distro-specific instructions on that page (usually a few `apt`/`dnf`
  commands).

After installing, **open Docker Desktop** and wait for it to say "Docker Desktop is running" (a
whale icon appears in your taskbar/menu bar — it should be steady, not animating/loading).

### Step 2: Verify Docker actually works

Open a terminal (Command Prompt, PowerShell, Terminal, or the terminal inside VS Code — doesn't
matter which) and run:

```bash
docker --version
docker compose version
```

Both should print a version number. If either says "command not found," Docker isn't installed
correctly or isn't on your PATH — restart your terminal (and your computer, if that doesn't fix
it) and try again.

### Step 3: Get the project onto your machine

If you downloaded `complaint-management-system.zip`:

```bash
cd ~/Downloads          # or wherever you saved it
unzip complaint-management-system.zip
cd complaint-management-system
```

(On Windows, right-click the zip → "Extract All" works fine instead of the `unzip` command.)

If you're pulling from GitHub instead:
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### Step 4: Get a Groq API key

1. Go to https://console.groq.com
2. Sign up / log in (free)
3. Find "API Keys" in the left sidebar → "Create API Key"
4. Copy the key immediately — it's usually only shown once

### Step 5: Create your `.env` file

Still in the project root (`complaint-management-system/`):

```bash
echo "GROQ_API_KEY=your_real_key_here" > .env
```

Replace `your_real_key_here` with the actual key you copied. On Windows, if `echo` gives you
trouble, just create a plain text file named `.env` (not `.env.txt`) in the project root
containing exactly one line: `GROQ_API_KEY=your_real_key_here`.

### Step 6: Build and start everything

```bash
docker compose up --build
```

First run takes a few minutes — it's downloading base images (Postgres, Python, Node, nginx) and
installing all dependencies inside the containers. You'll see a lot of scrolling text; that's
normal. Wait until the scrolling slows down and you see log lines like:

```
backend-1   | ... Complaint Management System starting in development mode
backend-1   | ... Database tables verified/created
```

Leave this terminal window open — it's running the live logs for all three services. Closing it
stops everything.

### Step 7: Confirm it's actually running

Open a **new** terminal window (leave the first one running) and check:

```bash
curl http://localhost:8000/health
```
Should return `{"status":"ok","app":"Complaint Management System","environment":"development"}`.

Then open these in your browser:
- **App**: http://localhost
- **API docs**: http://localhost:8000/docs

You should see the two-pane complaint form on the first, and interactive Swagger docs on the
second.

### Step 8: Try it with sample data

In the app at http://localhost, drag `sample_data/complaint_email_discoloration.eml` (from the
project folder) into the "AI Complaint Intake Assistant" panel on the right. Watch the fields on
the left populate automatically. See `SUBMISSION_GUIDE.md` for the full test checklist.

### Stopping it

Go back to the terminal running `docker compose up` and press `Ctrl+C`. To fully remove the
containers afterward (optional — keeps things tidy):
```bash
docker compose down
```
To start it again later, just run `docker compose up` (no `--build` needed unless you changed
code).

---

## Path B — Running natively, no Docker

Use this if Docker isn't an option for you.

### Step 1: Install Python 3.12+

Download from https://www.python.org/downloads/. **On Windows, check the box "Add Python to
PATH"** during install — this is the most common thing people miss.

Verify:
```bash
python3 --version     # Mac/Linux
python --version      # Windows
```
Should show `3.12.x` or higher.

### Step 2: Install Node.js 20+

Download the LTS version from https://nodejs.org/. npm comes bundled with it.

Verify:
```bash
node --version    # should show v20.x or higher
npm --version
```

### Step 3: Get the project (same as Path A, Step 3 above)

### Step 4: Set up the backend

```bash
cd backend
python3 -m venv venv
```

Activate the virtual environment:
```bash
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows (Command Prompt)
venv\Scripts\Activate.ps1      # Windows (PowerShell)
```
Your terminal prompt should now show `(venv)` at the start of the line.

```bash
pip install -r requirements.txt
```

Create your backend `.env`:
```bash
cp .env.example .env      # Mac/Linux
copy .env.example .env    # Windows
```
Open the new `backend/.env` in any text editor and fill in:
- `GROQ_API_KEY` — your real key from Path A, Step 4 above
- `DATABASE_URL` — easiest option if you don't want to install Postgres: change this line to
  `DATABASE_URL=sqlite:///./dev.db` (SQLite needs no separate database server at all)

Start the backend:
```bash
uvicorn app.main:app --reload
```
Leave this terminal running. You should see it start on `http://127.0.0.1:8000`. Confirm with
`curl http://localhost:8000/health` in another terminal, same as Path A Step 7.

### Step 5: Set up the frontend

Open a **new** terminal (leave the backend running in the first one):

```bash
cd complaint-management-system/frontend
npm install
npm run dev
```

This starts the Vite dev server, usually on `http://localhost:5173`. Open that URL in your
browser — the Vite dev server automatically proxies API calls to your backend on port 8000 (see
`frontend/vite.config.ts`), so both terminals need to stay running at the same time.

### Stopping it
`Ctrl+C` in each terminal. Next time, you only need to re-run `uvicorn app.main:app --reload`
and `npm run dev` — no need to redo `pip install`/`npm install` unless dependencies changed.

---

## Opening the project in VS Code

Either path, at any point:
```bash
cd complaint-management-system
code .
```
(or File → Open Folder in VS Code, and select the `complaint-management-system` folder)

VS Code doesn't run anything itself — it's just for reading/editing the code and using its
integrated terminal, which behaves exactly like the terminal instructions above. If you want,
install the **Python** and **Docker** extensions (search in the Extensions sidebar, `Ctrl+Shift+X`
/ `Cmd+Shift+X`) for nicer syntax highlighting and an easier way to view container logs — neither
is required for the project to run.

---

## Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| `docker compose up` fails immediately | Docker Desktop isn't actually running — check the whale icon |
| Port 80 or 8000 already in use | Something else on your machine is using that port; stop it, or edit the port mapping in `docker-compose.yml` (e.g. `"8080:80"` instead of `"80:80"`) |
| Frontend loads but AI extraction fails | Check `GROQ_API_KEY` is set correctly in `.env` (Path A) or `backend/.env` (Path B) — a missing/invalid key is the most common cause |
| `ModuleNotFoundError` (Path B) | Your virtual environment isn't activated — you should see `(venv)` in your prompt before running `uvicorn` |
| `npm install` fails on Windows | Make sure Node.js installed correctly (`node --version` works); try closing and reopening the terminal |
| Backend starts but DB errors appear | If using Postgres, make sure it's actually running and `DATABASE_URL` matches; easiest fix is switching to SQLite as described in Path B Step 4 |
