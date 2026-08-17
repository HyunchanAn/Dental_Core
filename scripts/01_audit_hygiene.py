import os
import subprocess
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(r"d:\Github")
REPORT_PATH = WORKSPACE_ROOT / "security_hygiene_report.md"
TOOLS_DIR = WORKSPACE_ROOT / "Dental_Core" / "scripts" / "tools"
GITLEAKS_EXE = "gitleaks"

# Repositories to check
REPOS = [WORKSPACE_ROOT / f"Dental_{i:03d}" for i in range(15)] + [
    WORKSPACE_ROOT / "Dental_Core",
    WORKSPACE_ROOT / "Dental_Panoramic_Reader"
]

def setup_gitleaks():
    global GITLEAKS_EXE
    try:
        subprocess.run(["gitleaks", "version"], capture_output=True, text=True, check=True)
        return "PATH/gitleaks"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    local_gitleaks = TOOLS_DIR / "gitleaks.exe"
    
    if not local_gitleaks.exists():
        print("[!] gitleaks not found in PATH or tools dir. Downloading gitleaks...")
        url = "https://github.com/gitleaks/gitleaks/releases/download/v8.21.1/gitleaks_8.21.1_windows_x64.zip"
        zip_path = TOOLS_DIR / "gitleaks.zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract("gitleaks.exe", TOOLS_DIR)
        zip_path.unlink()
        print("[O] gitleaks downloaded successfully.")

    GITLEAKS_EXE = str(local_gitleaks)
    return str(local_gitleaks)

def check_dependencies():
    print("=== Phase 0: Environment Bootstrap ===")
    deps = {
        "git": ["git", "--version"],
        "gh": ["gh", "--version"],
        "gh_auth": ["gh", "auth", "status"]
    }
    missing = []
    
    for dep, cmd in deps.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                print(f"[X] {dep} check failed.")
                missing.append(dep)
            else:
                print(f"[O] {dep} found.")
        except FileNotFoundError:
            print(f"[X] {dep} not found.")
            missing.append(dep)

    gitleaks_path = setup_gitleaks()
    print(f"[O] gitleaks found at: {gitleaks_path}")

    if missing:
        print("\n[CRITICAL] Missing dependencies. Exiting.")
        sys.exit(1)
    print("All dependencies satisfied.\n")

def check_repo(repo_path: Path):
    if not repo_path.exists() or not repo_path.is_dir():
        return None
    
    report = {
        "name": repo_path.name,
        "secrets": [],
        "large_files": [],
        "env_ignored": False,
        "readme_warning": False,
        "streamlit_bind": "N/A"
    }
    
    json_report = repo_path / "gitleaks-report.json"
    subprocess.run(f'"{GITLEAKS_EXE}" detect --source "{repo_path}" --report-format json --report-path "{json_report}"', capture_output=True, shell=True)
    
    if json_report.exists():
        try:
            with open(json_report, 'r', encoding='utf-8') as f:
                secrets_data = json.load(f)
                if secrets_data:
                    for s in secrets_data:
                        rule = s.get("RuleID", "Unknown")
                        file_path = s.get("File", "Unknown")
                        commit = s.get("Commit", "WorkingTree")[:7] if s.get("Commit") else "WorkingTree"
                        # Mask value implicitly by not including it in the output string
                        report["secrets"].append(f"[{rule}] in {file_path} (Commit: {commit}) - Value: ********")
            os.remove(json_report)
        except Exception:
            pass
    report["secrets"] = list(set(report["secrets"]))

    # Large files in history
    os.chdir(repo_path)
    git_rev_cmd = "git rev-list --objects --all"
    try:
        rev_out = subprocess.run(git_rev_cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore').stdout
        large_extensions = (".pt", ".pth", ".onnx")
        for line in rev_out.splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                filename = parts[1]
                if filename.endswith(large_extensions):
                    report["large_files"].append(filename)
    except Exception:
        pass
    report["large_files"] = list(set(report["large_files"]))
    
    # 3. .gitignore
    gitignore = repo_path / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding='utf-8', errors='ignore')
        if ".env" in content:
            report["env_ignored"] = True
            
    # 4. README warning
    readme = repo_path / "README.md"
    if readme.exists():
        content = readme.read_text(encoding='utf-8', errors='ignore').lower()
        if "연구용" in content and ("금지" in content or "로컬 전용" in content or "주의" in content):
            report["readme_warning"] = True

    # 5. Streamlit bind
    app_py = repo_path / "app.py"
    if app_py.exists():
        content = app_py.read_text(encoding='utf-8', errors='ignore')
        if "server.address" in content or "ALLOW_EXTERNAL_ACCESS" in content:
            if "0.0.0.0" in content and "ALLOW_EXTERNAL_ACCESS" not in content:
                report["streamlit_bind"] = "Hardcoded 0.0.0.0 (Unsafe)"
            else:
                report["streamlit_bind"] = "Configured"
        else:
            report["streamlit_bind"] = "Missing explicit bind"
            
    return report

def generate_report(results):
    lines = ["# Security & Hygiene Audit Report", ""]
    for r in results:
        lines.append(f"## {r['name']}")
        lines.append(f"- **Secrets Found**: {'[!] YES' if r['secrets'] else '[OK] None'}")
        if r['secrets']:
            for s in r['secrets'][:10]: # show up to 10
                lines.append(f"  - {s}")
            if len(r['secrets']) > 10:
                lines.append("  - ... (more)")
                
        lines.append(f"- **Large Models in History**: {'[!] YES' if r['large_files'] else '[OK] None'}")
        if r['large_files']:
            for f in r['large_files'][:5]:
                lines.append(f"  - {f}")
            if len(r['large_files']) > 5:
                lines.append("  - ... (more)")
                
        lines.append(f"- **.env Ignored**: {'[OK] Yes' if r['env_ignored'] else '[!] No'}")
        lines.append(f"- **README Warning**: {'[OK] Yes' if r['readme_warning'] else '[!] No'}")
        lines.append(f"- **Streamlit Bind**: {r['streamlit_bind']}")
        lines.append("")
        
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"\nReport generated at {REPORT_PATH}")

def main():
    check_dependencies()
    print("=== Phase 1: Auditing Repositories ===")
    
    valid_repos = [r for r in REPOS if r.exists() and r.is_dir()]
    print(f"Discovered {len(valid_repos)} valid repositories:")
    for r in valid_repos:
        print(f" - {r}")
    print("\nStarting scan...")
    
    results = []
    for r in valid_repos:
        res = check_repo(r)
        if res:
            results.append(res)
            print(f"[OK] Scanned {r.name}")
            
    generate_report(results)

if __name__ == "__main__":
    main()
