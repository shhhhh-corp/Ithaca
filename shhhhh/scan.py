import sys

from github import Github

from shhhhh.policies import main as scan_repo, POLICIES


def get_repos(gh_token):
    g = Github(gh_token)
    return g.get_user().get_repos()


def print_repos(repos):
    print(f"{len(repos)} repos detected:\n{', '.join(repo.full_name for repo in repos)}")


def print_policies():
    print("Scanning using these policies:")
    print("\n".join(pol.__doc__ for pol in POLICIES))


def main(gh_token):
    repos = list(get_repos(gh_token))
    print_repos(repos)
    print("-" * 20)

    print_policies()
    print("-" * 20)
    print()

    for repo in repos:
        scan_repo(gh_token, repo.full_name)


if __name__ == "__main__":
    gh_token = sys.argv[1]
    main(gh_token)
