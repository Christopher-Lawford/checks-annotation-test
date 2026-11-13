import json, os, subprocess, sys
repo = os.environ["REPO"]; sha = os.environ["HEAD_SHA"]
def api(path, body):
    r = subprocess.run(["gh","api","-X","POST",path,"--input","-"], input=json.dumps(body), capture_output=True, text=True)
    if r.returncode: print("ERR", path, r.stderr[:400]); return {}
    return json.loads(r.stdout)
def ann(path, line, msg): return {"path": path, "start_line": line, "end_line": line, "annotation_level": "failure", "message": msg, "title": f"T3:{path}:{line}"}
def run(name, anns):
    r = api(f"repos/{repo}/check-runs", {"name": name, "head_sha": sha, "status": "completed", "conclusion": "failure",
        "output": {"title": name, "summary": f"{len(anns)} annotations", "annotations": anns}})
    print(name, r.get("id"), r.get("html_url"))
run("T3 untouched-only", [ann("small.py", 3, "A1 untouched small.py line 3"), ann("small.py", 10, "A2 untouched small.py line 10")])
run("T3 mixed", [
  ann("untouched.py", 4, "A3 untouched.py line 4 (exists, not in diff)"),
  ann("todelete.py", 2, "B1 deleted file todelete.py line 2"),
  ann("torename.py", 2, "C1 OLD path torename.py line 2"),
  ann("renamed.py", 2, "C2 NEW path renamed.py line 2"),
  ann("ghost/nothere.py", 1, "D1 nonexistent path ghost/nothere.py"),
  ann("ws.py", 2, "E1 whitespace-only ws.py line 2"),
])
