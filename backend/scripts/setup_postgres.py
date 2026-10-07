import os
import sys
import urllib.request
import zipfile
import subprocess
import time

PG_ZIP_URL = "https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64-binaries.zip"
TARGET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pgsql"))
DATA_DIR = os.path.join(TARGET_DIR, "data")
ZIP_PATH = os.path.join(TARGET_DIR, "pgsql.zip")

def setup_postgres():
    os.makedirs(TARGET_DIR, exist_ok=True)
    bin_dir = os.path.join(TARGET_DIR, "bin")
    initdb_exe = os.path.join(bin_dir, "initdb.exe")
    pg_ctl_exe = os.path.join(bin_dir, "pg_ctl.exe")
    createdb_exe = os.path.join(bin_dir, "createdb.exe")

    if not os.path.exists(initdb_exe):
        if not os.path.exists(ZIP_PATH) or os.path.getsize(ZIP_PATH) < 100 * 1024 * 1024:
            print(f"Downloading PostgreSQL 16 binaries from {PG_ZIP_URL}...")
            req = urllib.request.Request(PG_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp, open(ZIP_PATH, "wb") as out:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"Downloading: {percent:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="\r")
            print("\nDownload complete.")
        print("Extracting zip archive...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            # The zip contains a top-level "pgsql" directory
            parent = os.path.abspath(os.path.join(TARGET_DIR, ".."))
            zip_ref.extractall(parent)
        print("Extraction finished.")

    # Initialize data cluster if not present
    if not os.path.exists(DATA_DIR) or not os.path.exists(os.path.join(DATA_DIR, "PG_VERSION")):
        print(f"Initializing PostgreSQL data cluster in {DATA_DIR}...")
        subprocess.run([
            initdb_exe,
            "-D", DATA_DIR,
            "-U", "postgres",
            "-E", "UTF8",
            "--auth-local=trust",
            "--auth-host=trust"
        ], check=True)
        print("Data cluster initialized.")

    # Start PostgreSQL service using pg_ctl
    print("Starting PostgreSQL server via pg_ctl...")
    log_file = os.path.join(TARGET_DIR, "logfile.log")
    subprocess.run([
        pg_ctl_exe,
        "-D", DATA_DIR,
        "-l", log_file,
        "start"
    ], check=True)
    time.sleep(2)

    # Create safevision_db if it doesn't exist
    print("Creating safevision_db database...")
    subprocess.run([
        createdb_exe,
        "-U", "postgres",
        "-h", "localhost",
        "-p", "5432",
        "safevision_db"
    ], capture_output=True)
    print("PostgreSQL is running and safevision_db is ready!")

if __name__ == "__main__":
    setup_postgres()
