import json, os, subprocess, sys
repo = os.environ["REPO"]; sha = os.environ["HEAD_SHA"]; pr = os.environ["PR"]
def api(method, path, body=None):
    cmd = ["gh", "api", "-X", method, path, "--input", "-"] if body is not None else ["gh", "api", "-X", method, path]
    r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    if r.returncode: print("ERR", path, r.stderr[:400]); sys.exit(1)
    return json.loads(r.stdout) if r.stdout.strip() else {}
def ann(path, line, msg, level="failure"):
    return {"path": path, "start_line": line, "end_line": line, "annotation_level": level, "message": msg, "title": f"T:{path}:{line}"}

# 1. placement test
basic = [
  ann("small.py", 21, "P1 IN-HUNK: small.py line 21 (changed)"),
  ann("small.py", 1, "P2 LINE-1 UNCHANGED: small.py line 1 (outside any hunk)"),
  ann("small.py", 38, "P3 OUTSIDE-HUNK: small.py line 38 (unchanged, far from hunk)"),
  ann("big.py", 1500, "P4 COLLAPSED: big.py line 1500 (fully rewritten large file)"),
  ann("big.py", 1, "P5 COLLAPSED LINE-1: big.py line 1"),
]
run = api("POST", f"repos/{repo}/check-runs", {"name": "TEST placement", "head_sha": sha, "status": "completed", "conclusion": "failure",
  "output": {"title": "Placement test", "summary": "5 annotations: in-hunk, line 1, outside hunk, collapsed file", "annotations": basic}})
print("placement run", run["id"], run["html_url"])

# 2. >50 annotations in batches of 50 via updates; 120 annotations on other.py changed lines 101-220
many = [ann("other.py", 100 + i, f"M{i:03d} other.py line {100+i}", "warning") for i in range(1, 121)]
run2 = api("POST", f"repos/{repo}/check-runs", {"name": "TEST many-annotations", "head_sha": sha, "status": "in_progress",
  "output": {"title": "120 annotations", "summary": "batched 50/50/20", "annotations": many[:50]}})
for k in (50, 100):
    api("PATCH", f"repos/{repo}/check-runs/{run2['id']}", {"output": {"title": "120 annotations", "summary": "batched 50/50/20", "annotations": many[k:k+50]}})
api("PATCH", f"repos/{repo}/check-runs/{run2['id']}", {"status": "completed", "conclusion": "failure"})
print("many run", run2["id"], run2["html_url"])

# 3. commit status alone
api("POST", f"repos/{repo}/statuses/{sha}", {"state": "failure", "context": "TEST status-only", "description": "commit status with no annotations"})

# 4. PR review comment on a changed line and an unchanged line
for line, tag in ((21, "in-hunk"), (38, "outside-hunk")):
    try:
        api("POST", f"repos/{repo}/pulls/{pr}/comments", {"body": f"TEST review comment {tag}", "commit_id": sha, "path": "small.py", "line": line, "side": "RIGHT"})
        print("review comment ok", tag)
    except SystemExit:
        print("review comment REJECTED", tag)
