#!/usr/bin/env python3
"""Open, inspect and squash-merge GitHub pull requests from the command line.

  scripts/pr.py open --gates 1,2,3,5,7 [--title T] [--what TEXT] [--why TEXT]
  scripts/pr.py list
  scripts/pr.py status <number>
  scripts/pr.py merge <number>

Token: ~/.config/smartpuck/github-token (fine-grained, this repo only).
`merge` refuses while any gate checkbox in the PR body is unticked and not marked n/a.
"""
import argparse, json, os, re, subprocess, sys, urllib.request, urllib.error

REPO = "schwim23/smartpuck"
API = f"https://api.github.com/repos/{REPO}"
TOKEN_FILE = os.path.expanduser("~/.config/smartpuck/github-token")
ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()

def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=ROOT, text=True, capture_output=True, check=check).stdout.strip()

def api(method, path, body=None):
    try:
        token = open(TOKEN_FILE).read().strip()
    except FileNotFoundError:
        sys.exit(f"No token at {TOKEN_FILE}")
    req = urllib.request.Request(API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "smartpuck-pr-cli"})
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API {method} {path} -> {e.code}: {e.read().decode()[:400]}")

def build_body(gates, what, why):
    tpl = open(os.path.join(ROOT, ".github/pull_request_template.md")).read()
    out = []
    for line in tpl.splitlines():
        m = re.match(r"- \[ \] Gate (\d+)", line)
        if m:
            line = line.replace("- [ ]", "- [x]", 1) if m.group(1) in gates else line + " — n/a"
        out.append(line)
    body = "\n".join(out)
    body = body.replace("## What changed\n", f"## What changed\n\n{what}\n", 1)
    body = body.replace("## Why\n", f"## Why\n\n{why}\n", 1)
    return body

def cmd_open(a):
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch == "main":
        sys.exit("On main. Create a feature branch first.")
    if git("status", "--porcelain"):
        sys.exit("Uncommitted changes. Commit first.")
    push = subprocess.run(["git", "push", "-u", "origin", branch], cwd=ROOT)  # runs pre-push gates
    if push.returncode:
        sys.exit("Push failed (see gate output above). PR not opened.")
    log = git("log", "--format=- %s", f"origin/main..{branch}")
    title = a.title or git("log", "-1", "--format=%s")
    body = build_body(set(a.gates.split(",")) if a.gates else set(), a.what or log, a.why or "")
    existing = api("GET", f"/pulls?head=schwim23:{branch}&state=open")
    if existing:  # updating: keep the PR's title unless --title was given
        title = a.title or existing[0]["title"]
        pr = api("PATCH", f"/pulls/{existing[0]['number']}", {"title": title, "body": body})
    else:
        pr = api("POST", "/pulls", {"title": title, "head": branch, "base": "main", "body": body})
    print(f"PR #{pr['number']}: {pr['title']}\n{pr['html_url']}")

def cmd_list(a):
    for pr in api("GET", "/pulls?state=open"):
        print(f"#{pr['number']}  {pr['head']['ref']}  {pr['title']}")

def unticked(body):
    return [l.strip() for l in (body or "").splitlines()
            if re.match(r"\s*- \[ \]", l) and "n/a" not in l.lower()]

def cmd_status(a):
    pr = api("GET", f"/pulls/{a.number}")
    files = api("GET", f"/pulls/{a.number}/files")
    print(f"#{pr['number']} {pr['title']}  [{pr['state']}{', merged' if pr.get('merged') else ''}]")
    print(f"mergeable: {pr.get('mergeable')}  ({pr.get('mergeable_state')})")
    for f in files:
        print(f"  {f['status']:<9} +{f['additions']:<4} -{f['deletions']:<4} {f['filename']}")
    bad = unticked(pr["body"])
    print("gates: all ticked or n/a" if not bad else "unticked:\n  " + "\n  ".join(bad))
    print(pr["html_url"])

def cmd_merge(a):
    pr = api("GET", f"/pulls/{a.number}")
    if pr["state"] != "open":
        sys.exit(f"PR #{a.number} is {pr['state']}.")
    bad = unticked(pr["body"])
    if bad:
        sys.exit("Refusing to merge; unticked gates:\n  " + "\n  ".join(bad))
    branch = pr["head"]["ref"]
    res = api("PUT", f"/pulls/{a.number}/merge",
              {"merge_method": "squash", "commit_title": f"{pr['title']} (#{a.number})"})
    print(res.get("message", "merged"), res.get("sha", "")[:7])
    api("DELETE", f"/git/refs/heads/{branch}")
    git("switch", "main"); git("pull", "--prune")
    git("branch", "-D", branch, check=False)
    print(f"main now at {git('log', '-1', '--format=%h %s')}; branch {branch} deleted")

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
s = p.add_subparsers(dest="cmd", required=True)
o = s.add_parser("open"); o.add_argument("--gates", default=""); o.add_argument("--title")
o.add_argument("--what"); o.add_argument("--why"); o.set_defaults(f=cmd_open)
s.add_parser("list").set_defaults(f=cmd_list)
st = s.add_parser("status"); st.add_argument("number", type=int); st.set_defaults(f=cmd_status)
m = s.add_parser("merge"); m.add_argument("number", type=int); m.set_defaults(f=cmd_merge)
a = p.parse_args(); a.f(a)
