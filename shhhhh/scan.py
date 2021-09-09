import sys

import yaml
from github import Github

from shhhhh.policies import POLICIES
from shhhhh.policies import main as scan_repo


def get_repos(gh_token, org_name=None):
    g = Github(gh_token)
    user = g.get_user()
    if org_name:
        [org] = [o for o in user.get_orgs() if o.login == org_name]
        return org.get_repos()

    return user.get_repos()


def print_repos(repos):
    print("repos detected:")
    for i, repo in enumerate(repos):
        print(f"{i+1}. {repo.full_name}")


def print_policies():
    print("Scanning using these policies:")
    print("\n".join(pol.__doc__ for pol in POLICIES))


def main(gh_token):
    with open("./conf.yaml") as f:
        conf = yaml.safe_load(f)

    org_name = conf["org_details"]["name"]
    repos = list(get_repos(gh_token, org_name))
    print_repos(repos)
    print("-" * 20)
    print()

    print_policies()
    print("-" * 20)
    print()

    for repo in repos:
        scan_repo(gh_token, repo.full_name)


if __name__ == "__main__":
    gh_token = sys.argv[1]
    main(gh_token)
