# coding: utf-8

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from distutils.util import strtobool

import yaml
from dateutil.parser import parse
from github import Github, UnknownObjectException
from jira import JIRA

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


def sca_tools_installed(repo, workflows=None):
    sca_tools = []
    if workflows is None:
        workflows = cicd_defined(repo)
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
        print(f"{repo.full_name} has no approved pipeline (no workflows found)")
        state["stop"] = True
        return state

    if repo_is_active(repo):
        if scas := sca_tools_installed(repo, state["workflows"]):
            state["sca"] = scas
            return state
        else:
            print(f"{repo.full_name} has no sca tools installed")

    state["stop"] = True
    return state


def sectool_supports_language(state):
    repo = state["repo"]
    repo_languages = repo.get_languages()
    sectools = state["sca"]
    for step in sectools:
        tool = step["uses"].split("@")[0]
        if SEC_TOOLS_LANG_SUPPORT[tool] not in repo_languages:
            print(
                f"{repo.full_name} has an SCA tool with language misconfigured - {tool}"
            )
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


def is_pr(gh_event):
    return "pull_request" in gh_event


def infrequent_committer(repo, gh_event):
    pr_num = gh_event["pull_request"]["number"]
    pr = repo.get_pull(pr_num)
    committers_to_this_pr = {commit.committer for commit in pr.get_commits()}

    # the "target" of this PR. The "last" commit on the target/base branch
    base_sha = pr.base.sha

    # commiters to base (i.e "main") branch:
    past_commiters = Counter(
        commit.committer
        for commit in repo.get_commits(
            base_sha, since=datetime.now() - timedelta(days=365)
        )
    )

    for pr_committer in committers_to_this_pr:
        # this committer has at least 2 commits already merged to the
        # base branch
        if past_commiters[pr_committer] < 2:
            offender = (
                pr_committer.login if hasattr(pr_committer, "login") else pr_committer
            )
            print(f"{offender} is a rare committer - requires expert review for code")
            return True

    return False


def _experts(repo, gh_event):
    """
    According to their past commits NUMBER, expert are the 4 most prolific committers."""
    # FIXME: implement real logic here
    # the "target" of this PR. The "last" commit on the target/base branch
    base_sha = gh_event["pull_request"]["base"]["sha"]

    # commiters to base (i.e "main") branch:
    past_commiters = Counter(
        commit.committer
        for commit in repo.get_commits(
            base_sha, since=datetime.now() - timedelta(days=365)
        )
    )
    MAGIC = 4
    return past_commiters.most_common(MAGIC)


def reviewed_by_expert(repo, gh_event):
    experts = _experts(repo, gh_event)
    pr_num = gh_event["pull_request"]["number"]
    pr = repo.get_pull(pr_num)
    for review in pr.get_reviews():
        if review.user in experts and review.state == "APPROVED":
            return True

    print("No expert reviewer approved this PR (yet?)")
    return False


def private_repos(repo):
    "All repos need to be private"
    return repo.private


def valid_cicd(repo):
    "All repos need to be covered by a CI/CD pipeline"
    return bool(cicd_defined(repo))


def sca_in_cicd(repo):
    "All repo piplines need to include an SCA test"
    return bool(sca_tools_installed(repo))


def sca_lang(repo):
    "The SCA checks in the pipeline must cover all repo programing languages"
    repo_languages = set(repo.get_languages())

    sectools = [step["uses"].split("@")[0] for step in sca_tools_installed(repo)]
    covered_languages = set(SEC_TOOLS_LANG_SUPPORT[tool] for tool in sectools)

    if uncovered := repo_languages - covered_languages:
        single_lang = len(uncovered) == 1
        print(
            f"{repo.full_name} has{' a' if single_lang else ''} programming "
            f"language{'s' if not single_lang else ''} ({', '.join(uncovered)}) "
            "not covered by any SCA tool"
        )
        return False

    return True


def sca_severity(repo):
    "SCA findings of high and above are not allowed"
    result = True
    for step in sca_tools_installed(repo):
        if not (step["uses"].split("@")[0]).startswith("snyk/actions"):
            # FIXME: only snyk is supported
            continue
        args = step.get("args", "")
        if "--severity-threshold=critical" in args:
            print(
                f"Snyk scan allows findings of severity \"high\" in step: {step.get('name', step.get('uses'))}"
            )
            result = False

    return result


def non_freq_committer(repo):
    "All commits by non-frequent contributers requiers an expet reviewer's approval"
    if "GITHUB_EVENT_PATH" not in os.environ:
        # not called from withing a github action. i.e from external script.
        # No commit so skipping
        print("Skipped, since this is not a pr")
        return True

    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        gh_event = json.load(f)

    if is_pr(gh_event) and infrequent_committer(repo, gh_event):
        return reviewed_by_expert(repo, gh_event)

    return True


def sca_ttl(repo):
    success = True
    try:
        jira = JIRA(
            server=os.environ["JIRA_URL"],
            basic_auth=(os.environ["JIRA_ACCESS_USER"], os.environ["JIRA_ACCESS_PW"]),
        )
        open_sca_issues = jira.search_issues(
            "labels = sca AND priority >= High AND status != Done"
        )
        for issue in open_sca_issues:
            more_than_2_days = (
                datetime.now(timezone.utc) - parse(issue.fields.created)
            ).days >= 2
            if more_than_2_days:
                print(
                    "found a high severity SCA issue that was not addressed within the TTL:"
                )
                print(f"{issue.key} was created on {parse(issue.fields.created)}")
                success = False

    except Exception:
        import traceback

        traceback.print_exc()

    return success  # FIXME: this is permissive.


def design_review(repo):
    try:
        jira = JIRA(
            server=os.environ["JIRA_URL"],
            basic_auth=(os.environ["JIRA_ACCESS_USER"], os.environ["JIRA_ACCESS_PW"]),
        )
        design_review_issues = jira.search_issues(
            "(text ~ security AND text ~ review AND text ~ design) AND status = Done"
        )
        n_design_reviews = len(design_review_issues)
        success = n_design_reviews > 0
        if success:
            issues = "\n".join([issue.key for issue in design_review_issues])
            print(
                f"found {n_design_reviews} security design review{'s' if n_design_reviews != 1 else ''}:"
            )
            print(issues)
        return success

    except Exception:
        import traceback

        traceback.print_exc()
        return True  # FIXME: this is permissive.


def cspm1(repo):
    # TODO
    return True


def cspm2(repo):
    # TODO
    return True


with open(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf.yaml"
    )
) as f:
    POLICIES = yaml.safe_load(f)["Policies"]


def _result_graphics(result):
    return f"""************
*** {'PASS' if result else 'FAIL'} ***
************"""


def main(gh_token, repo_name, fail_build=False, scan_mode=False):
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    all_good = True
    scan_results = []
    print(
        f"""
***********************************************
repo: {repo.full_name}
***********************************************"""
    )

    # start looping here
    for policy_idx, pol in enumerate(POLICIES):

        # FIXME: This ugliness is to support naming functions in the YAML.
        fn = globals()[pol["Policy"]["Code"]]

        print(
            f"""
Policy {policy_idx + 1}: {pol["Policy"]["Description"]}
repo: {repo.full_name}
"""
        )
        try:
            result = fn(repo)
            print(_result_graphics(result))
            sys.stdout.flush()
            scan_results.append(result)
            all_good &= result

        except Exception:
            import traceback

            traceback.print_exc()
            all_good = False

    if scan_mode:
        return scan_results

    if fail_build:
        return 0 if all_good else 1
    else:
        return 0


if __name__ == "__main__":
    gh_token, fail_build = sys.argv[1:3]
    sys.exit(main(gh_token, os.environ["GITHUB_REPOSITORY"], strtobool(fail_build)))
