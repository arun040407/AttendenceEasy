import os
import zipfile

ZIP_NAME = "AttendEasy_Cloud_Deploy.zip"
EXCLUDE_DIRS = {'__pycache__', '.venv', 'venv', 'env', '.git'}
EXCLUDE_EXTS = {'.pyc', '.pyo', '.log'}

def create_deploy_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, ZIP_NAME)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file == ZIP_NAME or file == "build_deploy_zip.py":
                    continue
                _, ext = os.path.splitext(file)
                if ext in EXCLUDE_EXTS:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                zipf.write(full_path, rel_path)
                
    print(f"Deployment package created: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path) / 1024:.1f} KB")

if __name__ == '__main__':
    create_deploy_zip()
