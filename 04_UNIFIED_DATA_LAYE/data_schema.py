# ============================================================
# D³ VITAL-X SPACE INTELLIGENCE PLATFORM
# Google Colab → GitHub Push
# Module 04: data_schema.py
# Version: 0.1.0 (Fixed Version)
# ============================================================

import os
import base64
import requests

from pathlib import Path
from google.colab import userdata


# ------------------------------------------------------------
# 1. GitHub Configuration
# ------------------------------------------------------------

GITHUB_TOKEN = userdata.get("GITHUB_TOKEN")

REPO_OWNER = "d3-vital-x"

# সংশোধিত সঠিক repository name
REPO_NAME = "D3-Vital-X-BANGLADESH-Workshop"

BRANCH = "main"

PROJECT_ROOT = Path(
    "/content/D3-VITAL-X-Space-Intelligence-Platform"
)

LOCAL_MODULE_DIR = PROJECT_ROOT / "04_UNIFIED_DATA_LAYER"

LOCAL_MODULE_PATH = (
    LOCAL_MODULE_DIR / "data_schema.py"
)

GITHUB_FILE_PATH = (
    "04_UNIFIED_DATA_LAYER/data_schema.py"
)


# ------------------------------------------------------------
# 2. Token & Directory Validation
# ------------------------------------------------------------

if not GITHUB_TOKEN:
    raise ValueError(
        "❌ GITHUB_TOKEN পাওয়া যায়নি। "
        "Colab → Secrets থেকে token সেট করুন।"
    )

# ডিরেক্টরি না থাকলে তৈরি করে নিবে
LOCAL_MODULE_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 3. Find data_schema.py Code from Colab History or Local File
# ------------------------------------------------------------

history = globals().get("In", [])
candidate_code = None

for cell_code in reversed(history):
    if (
        "class UnifiedDataRecord" in cell_code
        and "def create_unified_record" in cell_code
        and "def validate_schema" in cell_code
    ):
        candidate_code = cell_code
        break


# ------------------------------------------------------------
# 4. Save Module Locally
# ------------------------------------------------------------

if candidate_code:
    LOCAL_MODULE_PATH.write_text(
        candidate_code,
        encoding="utf-8"
    )
    print(f"✅ Local module saved from session history:\n{LOCAL_MODULE_PATH}")
elif LOCAL_MODULE_PATH.exists():
    print(f"ℹ️ Colab history-তে পাওয়া যায়নি, কিন্তু বিদ্যমান লোকাল ফাইল ব্যবহার করা হচ্ছে:\n{LOCAL_MODULE_PATH}")
else:
    raise RuntimeError(
        "❌ data_schema.py-এর মূল implementation পাওয়া যায়নি।\n"
        "প্রথমে data_schema.py কোড সেলটি চালান।"
    )


# ------------------------------------------------------------
# 5. GitHub API Configuration
# ------------------------------------------------------------

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

github_url = (
    f"https://api.github.com/repos/"
    f"{REPO_OWNER}/{REPO_NAME}/contents/"
    f"{GITHUB_FILE_PATH}"
)


# ------------------------------------------------------------
# 6. Read and Encode File
# ------------------------------------------------------------

with open(LOCAL_MODULE_PATH, "rb") as file:
    encoded_content = base64.b64encode(
        file.read()
    ).decode("utf-8")


# ------------------------------------------------------------
# 7. Check Existing GitHub File
# ------------------------------------------------------------

check_response = requests.get(
    github_url,
    headers=headers,
    params={"ref": BRANCH},
    timeout=30
)

if check_response.status_code == 200:
    existing_file = check_response.json()
    existing_sha = existing_file.get("sha")

    print("ℹ️ Existing GitHub file detected.")
    print("🔄 Update mode enabled.")

elif check_response.status_code == 404:
    existing_sha = None

    print("ℹ️ File does not exist on GitHub.")
    print("🆕 New file upload mode enabled.")

else:
    raise RuntimeError(
        "❌ GitHub file check failed.\n"
        f"Status: {check_response.status_code}\n"
        f"Response: {check_response.text}"
    )


# ------------------------------------------------------------
# 8. Prepare Upload Payload
# ------------------------------------------------------------

payload = {
    "message": (
        "Add Module 04 data_schema.py "
        "via Google Colab"
    ),
    "content": encoded_content,
    "branch": BRANCH
}

if existing_sha:
    payload["sha"] = existing_sha


# ------------------------------------------------------------
# 9. Push File to GitHub
# ------------------------------------------------------------

push_response = requests.put(
    github_url,
    headers=headers,
    json=payload,
    timeout=60
)


# ------------------------------------------------------------
# 10. Result Validation
# ------------------------------------------------------------

if push_response.status_code in [200, 201]:
    result = push_response.json()
    commit_info = result.get("commit", {})
    commit_sha = commit_info.get("sha", "Unavailable")

    print("\n" + "=" * 60)
    print("🎉 GITHUB PUSH SUCCESSFUL")
    print("=" * 60)

    print(f"📁 Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"🌿 Branch: {BRANCH}")
    print(f"📄 File: {GITHUB_FILE_PATH}")
    print(f"🔐 Commit SHA: {commit_sha}")

    print("\n✅ Module 04 successfully pushed to GitHub.")

else:
    print("\n" + "=" * 60)
    print("❌ GITHUB PUSH FAILED")
    print("=" * 60)

    print(f"HTTP Status: {push_response.status_code}")
    print(push_response.text)

    raise RuntimeError(
        "GitHub upload failed. "
        "Check repository name, token permission, "
        "branch, and file path."
    )
