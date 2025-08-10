import httpx


def fetch_github_issue_and_pr() -> dict:
    pr_url = "https://api.github.com/repos/DGP-Studio/Snap.Hutao.Docs/pulls?state=open"
    issue_url = "https://api.github.com/repos/DGP-Studio/Snap.Hutao/issues?state=open&labels=Publish"

    def check_label(item):
        labels = item["labels"]
        return len(list(filter(lambda label: label["name"] == "Document Updates", labels))) != 0

    prs = list(filter(check_label, httpx.get(pr_url).json()))
    issues = httpx.get(issue_url).json()

    if len(issues) == 0:
        print("No open issue with 'Publish' label at main repo.")
        raise IndexError
    elif len(issues) != 1:
        print("Too many open issue with 'Publish' label at main repo.")
        raise IndexError

    if len(prs) == 0:
        print("No open PR with 'Document Updates' label.")
        raise IndexError
    elif len(prs) != 1:
        print("Expected exactly one open PR with 'Document Updates' label.")
        raise IndexError

    return prs[0]
