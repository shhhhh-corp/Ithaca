import sys

import yaml
from github import Github
from piccup import html

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


def htmlize_repos(repos):
    div = ['div']
    div.append(['h2', 'Repos detected:'])
    div.append(['ol', {'type': 1},
                [['li', repo.full_name] for repo in repos]])
    return div


def print_policies():
    policies = [pol['Policy']['Description'] for pol in POLICIES]
    print("Scanning using these policies:")
    print("\n".join(policies))
    return policies


def htmlize_policies():
    policies = [pol['Policy']['Description'] for pol in POLICIES]

    div = ['div']
    div.append(['h2', 'Scanned using these policies:'])
    div.append(['ol', {'type': 1},
                [['li', policy] for policy in policies]])
    return div


def main(gh_token):
    head = ['head',
            ['title', 'Your OX report'],
            ['link', {'rel': "stylesheet", "href": "https://cdnjs.cloudflare.com/ajax/libs/tufte-css/1.8.0/tufte.min.css", "integrity": "sha512-F5lKjC1GKbwLFXdThwMWx8yF8TX/WVrdhWYN9PWb6eb5hIRLmO463nrpqLnEUHxy2EHIzfC4dq/mncHD6ndR+g==", "crossorigin": "anonymous", "referrerpolicy": "no-referrer"}],
            ['style', {'type': 'text/css'},
"""
td,
th {
    border: 1px solid rgb(190, 190, 190);
    padding: 10px;
}

td {
    text-align: center;
}

tr:nth-child(even) {
    background-color: #eee;
}

th[scope="col"] {
    background-color: #696969;
    color: #fff;
}

th[scope="row"] {
    background-color: #d7d9f2;
}

caption {
    padding: 10px;
    caption-side: bottom;
}

table {
    border-collapse: collapse;
    border: 2px solid rgb(200, 200, 200);
    letter-spacing: 1px;
    font-family: sans-serif;
    font-size: .8rem;
}
"""]]

    body = ['body', ['h1', 'Your OX report']]
    with open("./conf.yaml") as f:
        conf = yaml.safe_load(f)

    org_name = conf["org_details"]["name"]
    repos = list(get_repos(gh_token, org_name))
    print_repos(repos)
    body.append(htmlize_repos(repos))
    print("-" * 20)
    print()

    print_policies()
    print("-" * 20)
    print()

    table_head = ['thead',
                  ['tr',
                   ['th', {'scope': 'col'}, 'Repo'] +
                   [['th', {'scope': 'col'}, pol['Policy']['Name']] for pol in POLICIES]]]
    table_body = ['tbody']

    for repo in repos:
        scan_results = scan_repo(gh_token, repo.full_name, scan_mode=True)
        table_body.append(
            ['tr',
               ['th', {'scope': 'row'}, repo.full_name] +
               [['td', {'bgcolor': 'lightgreen' if result else 'red'}, 'PASS' if result else 'FAIL'] for result in scan_results]])


    table = ['table', table_head, table_body]
    body.extend([['h2', 'Scan results'], table])

    body.append(htmlize_policies())

    with open('./report.html', 'w') as f:
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
        f.write(html(['html', {"lang": "en", "xml:lang": "en",
                               "xmlns": "http://www.w3.org/1999/xhtml"},
                      [head,
                       body]]))
        print("report saved to report.html")


if __name__ == "__main__":
    gh_token = sys.argv[1]
    main(gh_token)
