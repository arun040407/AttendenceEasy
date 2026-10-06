# Cloud Deployment Guide for AttendEasy

This guide walks you through deploying **AttendEasy** to the cloud so anyone can access it online via a public URL (e.g. `https://attendeasy.onrender.com` or `https://yourname.pythonanywhere.com`).

---

## 🚀 Option 1: Render.com (Recommended - 100% Free with HTTPS)

Render is one of the most popular modern cloud hosts with free SSL certificates and automatic deployments.

### Step 1: Create a GitHub Repository
1. Go to [https://github.com/new](https://github.com/new) and log in.
2. Name the repository (e.g., `attendeasy`) and choose **Public** or **Private**.
3. Click **Create repository**.
4. On the next screen, click the link that says **"uploading an existing file"**.
5. Drag and drop all the files from this folder (`app.py`, `wsgi.py`, `database.py`, `templates`, `static`, `requirements.txt`, `Procfile`, `render.yaml`, etc.) into GitHub.
6. Click **Commit changes**.

### Step 2: Deploy on Render
1. Visit [https://render.com](https://render.com) and create a free account (you can sign in with your GitHub account).
2. On your Render dashboard, click the **New +** button in the top right and select **Web Service**.
3. Under **Connect a repository**, choose your `attendeasy` GitHub repository.
4. Render will automatically detect the settings from our configured `render.yaml` and `Procfile`:
   - **Name**: `attendeasy` (or any name you prefer)
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python seed_data.py`
   - **Start Command**: `gunicorn wsgi:app`
   - **Instance Type**: **Free**
5. Click **Create Web Service**.
6. Wait 1 to 2 minutes for the build to finish. Once done, you will receive your live URL:
   ```text
   https://attendeasy.onrender.com
   ```
   Anyone with this link can now enter attendance, view monthly quotas, and download reports!

---

## 🐍 Option 2: PythonAnywhere (No GitHub needed - Direct Browser Upload)

If you don't want to create a GitHub repository, **PythonAnywhere** lets you upload the project files directly through your web browser.

### Step 1: Sign up
1. Go to [https://www.pythonanywhere.com](https://www.pythonanywhere.com) and sign up for a free "Beginner" account.

### Step 2: Upload Project ZIP
1. In this folder, we have already packaged everything for you into **`AttendEasy_Cloud_Deploy.zip`**.
2. In PythonAnywhere, go to the **Files** tab.
3. Click **Upload a file** and upload `AttendEasy_Cloud_Deploy.zip`.
4. Open a **Bash console** on PythonAnywhere and run:
   ```bash
   unzip AttendEasy_Cloud_Deploy.zip
   pip install -r requirements.txt
   python seed_data.py
   ```

### Step 3: Configure Web App
1. Go to the **Web** tab in PythonAnywhere.
2. Click **Add a new web app** -> Choose **Manual configuration** -> Select **Python 3.12**.
3. In the **Code** section, set the **Source code** directory to `/home/yourusername`.
4. Click on the **WSGI configuration file** link to edit it. Replace its contents with:
   ```python
   import sys
   path = '/home/yourusername'
   if path not in sys.path:
       sys.path.append(path)

   from app import app as application
   ```
5. Click the green **Reload** button at the top of the Web tab.
6. Your application is now live at:
   ```text
   https://yourusername.pythonanywhere.com
   ```

---

## 🐳 Option 3: Deploy with Docker (Railway / Fly.io / VPS)

If you use a cloud container platform (like Railway, Fly.io, or your own Linux VPS):
1. The project already includes a production-ready **`Dockerfile`**.
2. Run locally or on your server:
   ```bash
   docker build -t attendeasy .
   docker run -d -p 5000:5000 attendeasy
   ```

---

## 📦 What files were prepared for your deployment:

- **`wsgi.py`**: Production entrypoint for Gunicorn and WSGI servers.
- **`Procfile`**: Tells cloud hosts to run the app using `gunicorn wsgi:app`.
- **`render.yaml`**: Pre-configured build instructions for 1-click Render hosting.
- **`runtime.txt`**: Specifies Python 3.12 for cloud platform runtimes.
- **`Dockerfile`**: Container recipe for Docker-based platforms.
- **`AttendEasy_Cloud_Deploy.zip`**: Ready-to-upload complete archive.
- **`prod_server.py`**: High-performance local WSGI server powered by Waitress.
