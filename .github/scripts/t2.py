import json, os, subprocess, sys
repo=os.environ["REPO"]; sha=os.environ["HEAD_SHA"]
scen=open("scenario.txt").read().strip()
def api(m,p,b=None):
    c=["gh","api","-X",m,p]+(["--input","-"] if b is not None else [])
    r=subprocess.run(c,input=json.dumps(b) if b is not None else None,capture_output=True,text=True)
    if r.returncode: print("ERR",p,r.stderr[:300]); sys.exit(1)
    return json.loads(r.stdout) if r.stdout.strip() else {}
def A(path,line,msg,lvl="warning"):
    return {"path":path,"start_line":line,"end_line":line,"annotation_level":lvl,"message":msg,"title":msg}
def run(name,anns):
    r=api("POST",f"repos/{repo}/check-runs",{"name":name,"head_sha":sha,"status":"in_progress","output":{"title":name,"summary":f"{len(anns)} annotations","annotations":anns[:50]}})
    for k in range(50,len(anns),50):
        api("PATCH",f"repos/{repo}/check-runs/{r['id']}",{"output":{"title":name,"summary":f"{len(anns)} annotations","annotations":anns[k:k+50]}})
    api("PATCH",f"repos/{repo}/check-runs/{r['id']}",{"status":"completed","conclusion":"failure"})
    print(name,r["id"],r["html_url"])
if scen=="s1":
    run("T2 s1-single-120",[A("a.py" if i<=60 else "b.py",i if i<=60 else i-60,f"Q1-{i:03d}") for i in range(1,121)])
elif scen=="s2":
    run("T2 s2-run1-30",[A("a.py",i,f"Q2a-{i:03d}") for i in range(1,31)])
    run("T2 s2-run2-30",[A("a.py",30+i,f"Q2b-{i:03d}") for i in range(1,31)])
    run("T2 s2-run3-60",[A("b.py",i,f"Q2c-{i:03d}") for i in range(1,61)])
elif scen=="s3":
    run("T2 s3-onefile-60",[A("c.py",i,f"Q3-{i:03d}") for i in range(1,61)])
elif scen=="s4":
    run("T2 s4-ordering-80",[A("a.py",i,f"Q4n-{i:03d}","notice") for i in range(1,41)]+[A("b.py",i,f"Q4f-{i:03d}","failure") for i in range(1,41)])
