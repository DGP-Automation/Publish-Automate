import json
import os

import httpx

from utils import fetch_github_issue_and_pr

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/DGP-Studio/Snap.Hutao/releases/latest"

new_version = os.getenv("VERSION")

github_version = httpx.get(GITHUB_LATEST_RELEASE_API).json()["tag_name"]
msix_file_name = f"Snap.Hutao.{new_version}.msix"


def get_update_logs(pr) -> tuple[str, str]:
    pr_title = pr["title"]
    ref_name = pr["head"]["ref"]
    if new_version not in pr_title:
        print(f"Wrong version in title: {pr_title}")
        raise NameError
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
    generic_changelog = f"""## 📘 更新日志
    
{zh_log}
    
## 📙 Update Log
    
{en_log}
    
## 📚 完整更新日志 Full Changelog


<details>
<summary><b>点击展开 Click to Expand</b></summary>


[From {github_version} to {new_version}](https://github.com/DGP-Studio/Snap.Hutao/compare/{github_version}.\
..{new_version})


</details>


## 镜像下载 Mirror Download


> 除了 GitHub 外，您还可以通过以下镜像下载 Snap Hutao 的最新版本
> In addition to GitHub, you can also download the latest version of Snap Hutao from the following mirrors


<a href="https://pan.quark.cn/s/d73ceb415ad9" style="text-decoration: none;" target="_blank">
  <img src="https://github.com/user-attachments/assets/b4755b8b-3cc4-441f-865b-2178faeb8398" width="16" height="16" />
  <span>  夸克网盘 Quark Drive</span>
</a>

<br>

"""


    generic_changelog = generic_changelog.replace("\n\n\n", "\n")
    generic_changelog = generic_changelog.replace("\n\n", "\n")
    social_promotion = f"""
{new_version} 版本已发布/ Version {new_version} is released

Release Page: https://github.com/DGP-Studio/Snap.Hutao/releases/tag/{new_version}
Direct Download: https://github.com/DGP-Studio/Snap.Hutao/releases/download/{new_version}/{msix_file_name}   
"""
    social_promotion = social_promotion + "\n" + generic_changelog
    ann_meta = {
        "title": f"{new_version} 版本已发布/Version {new_version} is Live",
        "description": f"{new_version} 版本已发布，请及时更新，点击查看详情可阅读完整更新日志\nVersion {new_version} is released"
                       f", please update as soon as possible. Click to view details to read the full "
                       f"changelog",
        "url": f"https://github.com/DGP-Studio/Snap.Hutao/releases/tag/{new_version}"
    }
    ann_meta = json.dumps(ann_meta, indent=2, ensure_ascii=False)
    return {
        "generic": generic_changelog,
        "social": social_promotion,
        "ann_meta": ann_meta
    }


def main():
    pr = fetch_github_issue_and_pr()
    en_log, zh_log = get_update_logs(pr)
    changelog_set = generate_changelog(en_log, zh_log)
    with open("release_body.md", "w") as body:
        body.writelines(changelog_set['generic'])


if __name__ == "__main__":
    main()
