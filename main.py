import json
import httpx
import os

from utils import send_zulip_message

PAT_TOKEN = os.getenv("PAT_TOKEN")

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"

new_version = os.getenv("VERSION")

github_version = httpx.get(GITHUB_LATEST_RELEASE_API).json()["tag_name"]
msix_file_name = f"Snap.Hutao.{new_version}.msix"


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


def main():
    en_log, zh_log = get_update_logs()
    changelog_set = generate_changelog(en_log, zh_log)
    message = f"{new_version} version is released, please process the following information:\n\n"
    for k, v in changelog_set.items():
        message += f"{k} message:\n\n```\n{v}\n```\n\n"
    send_zulip_message(message)
    # merge_docs_pull_request()
    os.putenv("GITHUB_OUTPUT", f"changelog={changelog_set['generic']}")


if __name__ == "__main__":
    main()
