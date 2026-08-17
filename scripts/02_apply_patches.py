import os
import subprocess
import time
from pathlib import Path

WORKSPACE_ROOT = Path(r"d:\Github")

REPOS = [WORKSPACE_ROOT / f"Dental_{i:03d}" for i in range(15)] + [
    WORKSPACE_ROOT / "Dental_Core",
    WORKSPACE_ROOT / "Dental_Panoramic_Reader"
]

GITIGNORE_APPEND = """
# Security & Hygiene
.env
*.pt
*.pth
*.onnx
__pycache__/
.venv/
"""

README_APPEND = """
## 연구용 실행 주의사항
- 기본 실행 주소: 127.0.0.1 (로컬 전용)
- 외부 공개/상용 배포 금지
- API 키·토큰은 환경변수로만 관리
- 오픈 데이터셋 외 민감 의료데이터 사용 금지
- 외부 접근이 필요하면 ALLOW_EXTERNAL_ACCESS=true 로만 명시적 허용
"""

STREAMLIT_BIND_BLOCK = """import os
if not os.getenv("ALLOW_EXTERNAL_ACCESS", "false").lower() == "true":
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
else:
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
"""

def apply_gitignore(repo_path: Path) -> bool:
    gitignore = repo_path / ".gitignore"
    content = ""
    if gitignore.exists():
        content = gitignore.read_text(encoding='utf-8', errors='ignore')
    
    if ".env" not in content:
        with open(gitignore, "a", encoding="utf-8") as f:
            if content and not content.endswith("\n"):
                f.write("\n")
            f.write(GITIGNORE_APPEND)
        return True
    return False

def apply_readme(repo_path: Path) -> bool:
    readme = repo_path / "README.md"
    if readme.exists():
        content = readme.read_text(encoding='utf-8', errors='ignore')
        if "연구용 실행 주의사항" not in content:
            with open(readme, "a", encoding="utf-8") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(README_APPEND)
            return True
    return False

def apply_streamlit_bind(repo_path: Path) -> bool:
    app_py = repo_path / "app.py"
    if app_py.exists():
        content = app_py.read_text(encoding='utf-8', errors='ignore')
        if "STREAMLIT_SERVER_ADDRESS" not in content and "ALLOW_EXTERNAL_ACCESS" not in content:
            # Prepend the block
            with open(app_py, "w", encoding="utf-8") as f:
                f.write(STREAMLIT_BIND_BLOCK + "\n" + content)
            return True
    return False

def enable_github_security(repo_path: Path) -> str:
    # Get repo name
    os.chdir(repo_path)
    res = subprocess.run('gh repo view --json nameWithOwner -q .nameWithOwner', capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
    if res.returncode != 0:
        return "Failed to get repo info from gh"
    repo_name = res.stdout.strip()
    
    # Try to enable secret scanning and dependabot
    cmd1 = f'gh api -X PUT repos/{repo_name}/vulnerability-alerts'
    cmd2 = f'gh api -X PATCH repos/{repo_name} -F "security_and_analysis[secret_scanning][status]=enabled"'
    
    res1 = subprocess.run(cmd1, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
    time.sleep(2) # throttle
    res2 = subprocess.run(cmd2, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
    time.sleep(2) # throttle
    
    status = []
    if res1.returncode == 0:
        status.append("Dependabot: OK")
    else:
        status.append(f"Dependabot: FAIL ({res1.stderr.strip()})")
        
    if res2.returncode == 0:
        status.append("SecretScanning: OK")
    else:
        status.append(f"SecretScanning: FAIL ({res2.stderr.strip()})")
        
    return ", ".join(status)

def main():
    print("=== Phase 2: Applying Patches ===")
    
    report_lines = ["# Phase 2 Patch Report\n"]
    
    valid_repos = [r for r in REPOS if r.exists() and r.is_dir()]
    
    for r in valid_repos:
        print(f"Patching {r.name}...")
        modifications = []
        
        if apply_gitignore(r):
            modifications.append(".gitignore appended")
        
        if apply_readme(r):
            modifications.append("README.md appended")
            
        if apply_streamlit_bind(r):
            modifications.append("app.py (Streamlit bind) patched")
            
        # GitHub API
        gh_status = enable_github_security(r)
        
        report_lines.append(f"## {r.name}")
        if modifications:
            report_lines.append("- **Files Patched**:")
            for m in modifications:
                report_lines.append(f"  - {m}")
        else:
            report_lines.append("- **Files Patched**: None (Already compliant)")
            
        report_lines.append(f"- **GitHub API**: {gh_status}\n")

    report_path = WORKSPACE_ROOT / "phase2_patch_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\nDone! Patch report saved to {report_path}")
    
    # Run git diff --stat across all to show what changed
    print("\n=== Working Tree Changes (git diff --stat) ===")
    for r in valid_repos:
        os.chdir(r)
        diff_out = subprocess.run("git diff --stat", capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore').stdout.strip()
        if diff_out:
            print(f"[{r.name}]\n{diff_out}\n")

if __name__ == "__main__":
    main()
