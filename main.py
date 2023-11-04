import json
import httpx
import re
import os
from bs4 import BeautifulSoup
from utils import download_stream_file, send_zulip_message

PAT_TOKEN = os.getenv("PAT_TOKEN")

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"
MS_STORE_RELEASE_API = "https://store.rg-adguard.net/api/GetFiles"
MS_STORE_RELEASE_API_PARAMS = {
    "type": "ProductId",
    "url": "9PH4NXJ2JN52",
    "ring": "RP",
    "lang": "en-US"
}
FILE_NAME_REGEX = r"^60568DGPStudio\.SnapHutao_(?P<v>\d\.\d+\.\d+)\.0_x64__\w+\.msix"


def has_newer_version() -> (bool, str, str):
    github_version = httpx.get(GITHUB_LATEST_RELEASE_API).json()["tag_name"]
    ms_meta_soup = BeautifulSoup(httpx.post(MS_STORE_RELEASE_API, data=MS_STORE_RELEASE_API_PARAMS).text,
                                 "html.parser")
    ms_version = ms_meta_soup.find("a", string=re.compile(FILE_NAME_REGEX))
    ms_url = ms_version["href"]
    ms_version = re.search(FILE_NAME_REGEX, ms_version.text).group("v")
    github_version = [int(i) for i in github_version.split(".")]
    ms_version = [int(i) for i in ms_version.split(".")]

    if ms_version > github_version:
        print("New version detected")
        print(f"Current GitHub version: {github_version}")
        print(f"Current MS version: {ms_version}")
        return True, ms_url, ".".join([str(i) for i in ms_version])
    else:
        print("No new version detected")
    return False, None, None


def get_update_logs(expected_version: str) -> (str, str):
    pr_url = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Docs/pulls?state=open&labels=Document%20Updates"
    response = httpx.get(pr_url).json()
    if len(response) == 0:
        print("No open PR with 'Document Updates' label.")
        return None
    elif len(response) != 1:
        print("Expected exactly one open PR with 'Document Updates' label.")
        return None
    pr = response[0]
    pr_title = pr["title"]
    ref_name = pr["head"]["ref"]
    if pr_title != f"Update to {expected_version}":
        print(f"Expected PR title: 'Update to {expected_version}'")
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


def generate_changelog(en_log: str, zh_log: str, new_version: str):
    github_version = httpx.get(GITHUB_LATEST_RELEASE_API).json()["tag_name"]
    generic_changelog = f"""
## 更新日志
    
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
Direct Download: https://github.com/DGP-Studio/Snap.Hutao/releases/download/{new_version}/Snap.Hutao.{new_version}.msix   
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


def add_update_log_to_discord_queue(message: str) -> bool:
    url = "https://bot-webhook.snapgenshin.cn/private"
    data = {
        "type": "add_discord_message",
        "data": {
            "message": message
        }
    }
    response = httpx.post(url, json=data)
    print(response.status_code)
    print(response.text)
    return True


def create_release_and_upload_asset(tag_name: str, release_content: str) -> bool:
    repo_name = "DGP-Studio/Snap.Hutao"
    url = f"https://api.github.com/repos/{repo_name}/releases"
    post_body = {
        "tag_name": tag_name,
        "target_commitish": "main",
        "name": tag_name,
        "body": release_content,
        "draft": True,
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
        print(f"Unknown error: {response.status_code}")
        return False
    release_id = response.json()["id"]
    upload_url = response.json()["upload_url"]
    print(f"Release id: {release_id}")
    url = upload_url.replace("{?name,label}", f"?name=Snap.Hutao.{tag_name}.msix")
    print(f"Upload url: {url}")
    mimetypes = "application/msix"
    headers["Content-Type"] = mimetypes
    with open(f"./cache/Snap.Hutao.{tag_name}.msix", "rb") as f:
        data = f.read()
    response = httpx.post(url, content=data, headers=headers)
    print(f"Upload status code: {response.status_code}")


def main():
    check_result = has_newer_version()
    if not check_result[0]:
        return False
    print(f"Downloading Snap.Hutao.{check_result[2]}.msix")
    download_stream_file(check_result[1], f"Snap.Hutao.{check_result[2]}.msix")
    print("Downloading update logs")
    en_log, zh_log = get_update_logs(check_result[2])
    changelog_set = generate_changelog(en_log, zh_log, check_result[2])
    message = f"{check_result[2]} version is released, please process the following information:\n\n"
    for k, v in changelog_set.items():
        message += f"{k} message:\n\n```\n{v}\n```\n\n"
    send_zulip_message(message)
    merge_docs_pull_request()
    add_update_log_to_discord_queue(changelog_set["social"])
    create_release_and_upload_asset(check_result[2], changelog_set["generic"])


if __name__ == "__main__":
    main()
