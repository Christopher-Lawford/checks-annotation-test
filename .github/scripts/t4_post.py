import json, os, subprocess, sys
from ruamel.yaml import YAML
repo=os.environ["REPO"]; sha=os.environ["HEAD_SHA"]
def api(method,path,body):
    r=subprocess.run(["gh","api","-X",method,path,"--input","-"],input=json.dumps(body),capture_output=True,text=True)
    if r.returncode: print("ERR",path,r.stderr[:500]); sys.exit(1)
    return json.loads(r.stdout)
def ann(path,s,e,level,msg,**kw):
    d={"path":path,"start_line":s,"end_line":e,"annotation_level":level,"message":msg,"title":f"T4 {msg[:20]}"}; d.update(kw); return d
doc=YAML().load(open("contract.yaml"))
L=lambda node,key: node.lc.key(key)[0]+1       # 1-based line of a key
C=lambda node,key: node.lc.key(key)[1]+1
props=doc["schema"][0]["properties"]
vline=L(doc,"version"); vcol=doc.lc.value("version")[1]+1
print("version line",vline,"prop3 name line",L(props[3],"name"))
b=[]
# B1 version, in-hunk, with column range
b.append(ann("contract.yaml",vline,vline,"failure","B1 version in-hunk cols",start_column=vcol,end_column=vcol+5))
# B2 nested property (index 3 'quantity' changed) name line, in-hunk
b.append(ann("contract.yaml",L(props[3],"logicalType"),L(props[3],"logicalType"),"warning","B2 quantity.logicalType in-hunk"))
# B3 apiVersion line 1, out-of-hunk
b.append(ann("contract.yaml",L(doc,"apiVersion"),L(doc,"apiVersion"),"notice","B3 apiVersion line1 notice"))
# B4 far out-of-hunk: slaProperties key
b.append(ann("contract.yaml",L(doc,"slaProperties"),L(doc,"slaProperties"),"warning","B4 slaProperties out-of-hunk"))
# B5 multi-line range spanning changed + unchanged: property 3 start .. property 5 start-1
s=L(props[3],"name"); e=L(props[5],"name")-1
b.append(ann("contract.yaml",s,e,"failure",f"B5 range {s}-{e} spans changed+unchanged"))
# B6 multi-line range entirely unchanged: property 8 block
s=L(props[8],"name"); e=L(props[9],"name")-1
b.append(ann("contract.yaml",s,e,"notice",f"B6 range {s}-{e} all unchanged"))
# B7 column range on same line inside changed property description
dl=L(props[4],"description")
b.append(ann("contract.yaml",dl,dl,"warning","B7 price.description cols",start_column=C(props[4],"description"),end_column=C(props[4],"description")+11))
# B8 line number past end of file
b.append(ann("contract.yaml",999,999,"failure","B8 line 999 beyond EOF"))
# A: collapsed diff files
a=[ann("huge.txt",1,1,"failure","A1 huge.txt line 1"),
   ann("huge.txt",15000,15000,"failure","A2 huge.txt line 15000"),
   ann("pkg/package-lock.json",2500,2500,"warning","A3 lockfile line 2500"),
   ann("pkg/package-lock.json",1,1,"notice","A4 lockfile line 1")]
for name,anns in (("T4 contract-lines",b),("T4 collapsed-files",a)):
    r=api("POST",f"repos/{repo}/check-runs",{"name":name,"head_sha":sha,"status":"completed","conclusion":"failure","output":{"title":name,"summary":name,"annotations":anns}})
    print(name,r["id"],r["output"]["annotations_count"])
json.dump({"b":[(x["message"],x["start_line"],x["end_line"]) for x in b]},open("t4_lines.json","w"))
print(json.dumps([(x["message"][:12],x["start_line"],x["end_line"]) for x in b]))
