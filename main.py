import json
import httpx
import os
from utils import download_stream_file, send_zulip_message, calculate_file_sha512

SIGNPATH_TOKEN = os.getenv("SIGNPATH_TOKEN")
PAT_TOKEN = os.getenv("PAT_TOKEN")

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"

download_link = os.getenv("DOWNLOAD_LINK")
new_version = os.getenv("VERSION")

github_version = httpx.get(GITHUB_LATEST_RELEASE_API).json()["tag_name"]
msix_file_name = f"Snap.Hutao.{new_version}.msix"
msix_file_path = f"./cache/Snap.Hutao.{new_version}.msix"
sha512_file_name = "SHA512SUM"
sha512_file_path = f"./cache/SHA512SUM"


def generate_hash_file():
    with open(sha512_file_path, "w") as f:
        sha512 = calculate_file_sha512(msix_file_path)
        print(f"SHA512: {sha512}")
        f.writelines(f"{sha512} {msix_file_name}")


def get_update_logs() -> (str, str):
    pr_url = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Docs/pulls?state=open"

    def check_label(item):
        labels = item["labels"]
        return len(list(filter(lambda label: label["name"] == "Document Updates", labels))) != 0

    response = list(filter(check_label, httpx.get(pr_url).json()))

    if len(response) == 0:
        print("No open PR with 'Document Updates' label.")
        return None
    elif len(response) != 1:
        print("Expected exactly one open PR with 'Document Updates' label.")
        return None
    pr = response[0]
    pr_title = pr["title"]
    ref_name = pr["head"]["ref"]
    if pr_title != f"Update to {new_version}":
        print(f"Expected PR title: 'Update to {new_version}'")
        return None
    else:
        print(f"Found PR with 'Document Updates' label: {pr_title}, id: {pr['number']}")

    def get_raw_url(file_path: str) -> str | None:
        content_url = f"https://raw.githubusercontent.com/DGP-Studio/Snap.Hutao.Docs/{ref_name}/{file_path}"
        return content_url

    en_update_log_url = get_raw_url("docs/en/statements/update-log.md")
    en_update_log = httpx.get(en_update_log_url).text.split("##")[1].split("\n")
    en_update_log = "\n".join([s for s in en_update_log if "<Badge text=" not in s])
    print(f"En update log:\n{en_update_log}")

    zh_update_log_url = get_raw_url("docs/zh/statements/update-log.md")
    zh_update_log = httpx.get(zh_update_log_url).text.split("##")[1].split("\n")
    zh_update_log = "\n".join([s for s in zh_update_log if "<Badge text=" not in s])
    print(f"Zh update log:\n{zh_update_log}")

    return en_update_log, zh_update_log


def generate_changelog(en_log: str, zh_log: str):
    generic_changelog = f"""## 更新日志
    
{zh_log}
    
## Update Log
    
{en_log}
    
## 完整更新日志/What's Changed
    
Full Changelog: [{github_version}...{new_version}](https://github.com/DGP-Studio/Snap.Hutao/compare/{github_version}.\
..{new_version})
"""
    generic_changelog = generic_changelog.replace("\n\n\n", "\n")
    generic_changelog = generic_changelog.replace("\n\n", "\n")
    social_promotion = f"""
{new_version} 版本已发布于微软商店/ Version {new_version} is released on Microsoft Store

Release Page: https://github.com/DGP-Studio/Snap.Hutao/releases/tag/{new_version}
Direct Download: https://github.com/DGP-Studio/Snap.Hutao/releases/download/{new_version}/{msix_file_name}   
"""
    social_promotion = social_promotion + "\n" + generic_changelog
    ann_meta = {
        "title": f"{new_version} 版本已发布/Version {new_version} is Live",
        "description": f"{new_version} 版本已发布于微软商店，请及时更新，点击查看详情可阅读完整更新日志\nVersion {new_version} is released on "
                       f"Microsoft Store, please update as soon as possible. Click to view details to read the full "
                       f"changelog",
        "url": f"https://github.com/DGP-Studio/Snap.Hutao/releases/tag/{new_version}"
    }
    ann_meta = json.dumps(ann_meta, indent=2, ensure_ascii=False)
    return {
        "generic": generic_changelog,
        "social": social_promotion,
        "ann_meta": ann_meta
    }


def merge_docs_pull_request() -> bool:
    pr_url = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Docs/pulls?state=open&labels=Document%20Updates"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {PAT_TOKEN}",
    }
    response = httpx.get(pr_url, headers=headers).json()
    if len(response) != 1:
        print("Expected exactly one open PR with 'Document Updates' label.")
        return False
    pr = response[0]
    pr_title = pr["title"]
    if not pr_title.startswith("Update to "):
        print("Expected PR title: 'Update to x.x.x'")
        return False
    pr_number = pr["number"]
    pr_url = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Docs/pulls/{pr_number}/merge"
    merge_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {PAT_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = httpx.put(pr_url, headers=merge_headers)
    print(response.status_code)
    print(response.text)
    return True


def create_release_and_upload_asset(release_content: str) -> bool:
    repo_name = "DGP-Studio/Snap.Hutao"
    url = f"https://api.github.com/repos/{repo_name}/releases"
    post_body = {
        "tag_name": new_version,
        "target_commitish": "main",
        "name": new_version,
        "body": release_content,
        "draft": False,
        "prerelease": False,
        "make_latest": "true"
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {PAT_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = httpx.post(url, json=post_body, headers=headers)
    if response.status_code == 201:
        print("Release created")
    elif response.status_code == 422:
        print("Validation failed, or the endpoint has been spammed.")
        return False
    elif response.status_code == 404:
        print("Not Found if the discussion category name is invalid")
        return False
    else:
        print(f"Unknown error: {response.status_code}, {response.text}")
        return False
    release_id = response.json()["id"]
    upload_url = response.json()["upload_url"]
    print(f"Release id: {release_id}")
    print(f"Upload url: {upload_url}")

    def upload_asset(name, path):
        file_upload_url = upload_url.replace("{?name,label}", f"?name={name}")
        mimetypes = "application/octet-stream"
        headers["Content-Type"] = mimetypes
        files = {"upload_file": open(path, "rb")}
        resp = httpx.post(file_upload_url, files=files, headers=headers)
        print(f"Upload status code: {resp.status_code}")

    upload_asset(msix_file_name, msix_file_path)
    upload_asset(sha512_file_name, sha512_file_path)


def main():
    print(f"Downloading {msix_file_name}")
    download_stream_file(download_link, msix_file_name, {"Authorization": f"Bearer {SIGNPATH_TOKEN}"})
    generate_hash_file()
    print("Downloading update logs")
    en_log, zh_log = get_update_logs()
    changelog_set = generate_changelog(en_log, zh_log)
    message = f"{new_version} version is released, please process the following information:\n\n"
    for k, v in changelog_set.items():
        message += f"{k} message:\n\n```\n{v}\n```\n\n"
    send_zulip_message(message)
    merge_docs_pull_request()
    create_release_and_upload_asset(changelog_set["generic"])


if __name__ == "__main__":
    main()
