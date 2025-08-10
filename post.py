import os

import httpcore
import httpx

from utils import fetch_github_issue_and_pr

PAT_TOKEN = os.getenv("PAT_TOKEN")


def merge_docs_pull_request(pr):
    pr_number = pr["number"]
    pr_url = f"https://api.github.com/repos/DGP-Studio/Snap.Hutao.Docs/pulls/{pr_number}/merge"
    merge_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {PAT_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        response = httpx.put(pr_url, headers=merge_headers)
        print(response.status_code)
        print(response.text)
    except httpcore.ReadTimeout:
        print("Merge PR timeout.")
        try:
            print("Retry fetching PR.")
            pr = fetch_github_issue_and_pr()
            merge_docs_pull_request(pr)
        except IndexError:
            print("PR already merged.")
            pass


def main():
    pr = fetch_github_issue_and_pr()
    merge_docs_pull_request(pr)


if __name__ == "__main__":
    main()
