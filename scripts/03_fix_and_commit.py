import os
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(r"d:\Github")

REPOS = [WORKSPACE_ROOT / f"Dental_{i:03d}" for i in range(15)] + [
    WORKSPACE_ROOT / "Dental_Core",
    WORKSPACE_ROOT / "Dental_Panoramic_Reader"
]

STREAMLIT_BIND_BLOCK = """import os
if not os.getenv("ALLOW_EXTERNAL_ACCESS", "false").lower() == "true":
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
else:
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
"""

def fix_app_py(repo_path: Path):
    app_py = repo_path / "app.py"
    if app_py.exists():
        content = app_py.read_text(encoding='utf-8', errors='ignore')
        if STREAMLIT_BIND_BLOCK in content:
            new_content = content.replace(STREAMLIT_BIND_BLOCK + "\n", "")
            app_py.write_text(new_content, encoding='utf-8')
            print(f"Reverted app.py in {repo_path.name}")
            
def add_run_script(repo_path: Path):
    app_py = repo_path / "app.py"
    if app_py.exists():
        # Create run.py
        run_py = repo_path / "run.py"
        run_content = """import os
import sys
from streamlit.web import cli as stcli

if __name__ == "__main__":
    addr = "0.0.0.0" if os.getenv("ALLOW_EXTERNAL_ACCESS", "false").lower() == "true" else "127.0.0.1"
    sys.argv = ["streamlit", "run", "app.py", f"--server.address={addr}"]
    sys.exit(stcli.main())
"""
        run_py.write_text(run_content, encoding='utf-8')
        print(f"Added run.py in {repo_path.name}")

def commit_and_push(repo_path: Path):
    os.chdir(repo_path)
    subprocess.run("git add .", shell=True)
    res = subprocess.run('git commit -m "chore(security): apply research hygiene baselines"', shell=True, capture_output=True)
    if "nothing to commit" not in str(res.stdout):
        subprocess.run("git push", shell=True)
        print(f"Committed and pushed {repo_path.name}")
    else:
        print(f"Nothing to commit for {repo_path.name}")

def main():
    print("=== Fixing Streamlit and Committing ===")
    valid_repos = [r for r in REPOS if r.exists() and r.is_dir()]
    for r in valid_repos:
        # 1. Revert bad patch
        fix_app_py(r)
        
        # 2. Apply proper wrapper
        add_run_script(r)
        
        # 3. Commit and push
        commit_and_push(r)
        
    print("All repos committed and pushed.")

if __name__ == "__main__":
    main()
