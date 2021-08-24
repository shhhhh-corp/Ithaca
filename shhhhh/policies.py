# coding: utf-8

import os
import sys
from collections import Counter

import yaml
from github import Github, UnknownObjectException

# we're also checking for gh workflows, using the api
CICD_CONFIG_FILES = ("Jenkinsfile", ".circleci/config.yml")

SEC_TOOLS_LANG_SUPPORT = {
    "snyk/actions": "JavaScript",
    "snyk/actions/cocoapods": "Swift",
    "snyk/actions/dotnet": "C#",
    "snyk/actions/golang": "Go",
    "snyk/actions/gradle": "Java",
    "snyk/actions/maven": "Java",
    "snyk/actions/node": "JavaScript",
    "snyk/actions/php": "PHP",
    "snyk/actions/python": "Python",
    "snyk/actions/ruby": "Ruby",
    "snyk/actions/scala": "Scala",
    "snyk/actions/docker": "Docker",
    "snyk/actions/iac": "terraform",
}


def cicd_defined(repo):
    for config_file in CICD_CONFIG_FILES:
        found = None
        try:
            # FIXME: currently, not supported
            found = repo.get_contents(config_file)
            return found
        except UnknownObjectException:
            continue

    if not found:
        return list(repo.get_workflows())


def repo_is_active(repo):
    # FIXME
    return True


def sca_tools_installed(repo, workflows):
    sca_tools = []
    # FIXME: only currently supports GH Actions
    for workflow in workflows:
        try:
            # FIXME: use the git repo itself, not api call
            for job in yaml.safe_load(repo.get_contents(workflow.path).decoded_content)[
                "jobs"
            ].values():
                for step in job["steps"]:
                    action = step.get("uses", "")
                    if action.startswith("whitesource/GitHubPackagesSecurityAction"):
                        sca_tools.append(step)
                    elif action.startswith("snyk/actions"):
                        sca_tools.append(step)
        except Exception:
            continue

    return sca_tools


def approved_pipeline(state):
    """
    **** find a CICD file (circle, GH actions, etc.)
    **** Make sure the repo is active (by last commit/last build)
    **** Ensure either snyk or whitesource in the CICD file
    """
    repo = state["repo"]
    if workflows := cicd_defined(repo):
        state["workflows"] = workflows
    else:
        print(f"{repo.name} has no approved pipeline (no workflows found)")
        state["stop"] = True
        return state

    if repo_is_active(repo):
        if scas := sca_tools_installed(repo, state["workflows"]):
            state["sca"] = scas
            return state
        else:
            print(f"{repo.name} has no sca tools installed")

    state["stop"] = True
    return state


def sectool_supports_language(state):
    repo = state["repo"]
    repo_languages = repo.get_languages()
    sectools = state["sca"]
    for step in sectools:
        tool = step["uses"].split("@")[0]
        if SEC_TOOLS_LANG_SUPPORT[tool] not in repo_languages:
            print(f"{repo.name} has an SCA tool with language misconfigured - {tool}")
            state["stop"] = True

    return state


def high_findings_break_build(state):
    sectools = state["sca"]
    for step in sectools:
        args = step.get("with", {}).get("args", "")
        if "--severity-threshold=critical" in args:
            # this means "high" severity vulns will not be reported,
            # letting the build continue in contradiction of the policy
            state["stop"] = True

    return state


def rule1(repo):
    """
    * Rule 1
    ** All github repos have approved CICD pipeline
    *** scan all the org's repos. For each repo,
    **** find a CICD file (circle, GH actions, etc.)
    **** Make sure the repo is active (by last commit/last build)
    **** Ensure either snyk or whitesource in the CICD file
    ** Security tool used for each repo supports its programming language
    ** Ensure findings of level "high" or more will break the build
    """
    state = {"repo": repo, "stop": False}
    for func in (
        approved_pipeline,
        sectool_supports_language,
        high_findings_break_build,
    ):
        state = func(state)
        if state["stop"]:
            return False

    print("Policy 1 passed 👍")
    return True


def rare_committer(repo):
    "Is the LATEST committer new to this repo?"
    # FIXME: should not look at the latest committer but get a
    # commit. This will work better once it's implemented as a GH
    # action, not a standalone script.

    # TODO:
    # 1. less than 3 merged PRs in the last year, they are a
    # rare committer and FAIL the build.
    # 2. Find the 3 most common reviewers on this repo, and add them
    # as reviewers.

    commits_itr = repo.get_commits().__iter__()
    latest_committer_fixme = next(commits_itr).committer
    past_commiters = Counter(commit.committer for commit in commits_itr)
    if latest_committer_fixme not in past_commiters:
        print(f"{latest_committer_fixme} is NEW to this repo ⁄ ⁄•⁄ω⁄•⁄ ⁄")
        return False
    print("Not a rare committer 👍")
    return True


def policy1(repo):
    return repo.private



def _result_graphics(repo_name, result):
    return """************
*** {if result "PASS" else "FAIL"} ***
************"""


def main(gh_token, repo_name):
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    all_good = True
    print(f"""
***********************************************
repo: {repo.name}
***********************************************""")

    # start looping here
    print(f"""
Policy 1: All repos need to be private
repo: {repo.name}""")
    try:
        result = policy1(repo)  # rule1(repo) and rare_committer(repo)
    except Exception:
        import traceback

        traceback.print_exc()
        result = False

    print(_result_graphics(repo.name, result))
    all_good &= result

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], os.environ["GITHUB_REPOSITORY"]))
