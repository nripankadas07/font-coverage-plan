"""Exercise the installed wheel's actual console entry point outside this checkout."""
import hashlib, json, os, pathlib, shutil, sqlite3, subprocess, sys, tempfile

SOURCE=pathlib.Path(__file__).absolute().parent
PYTHON=pathlib.Path(sys.argv[1]).absolute()  # Do not resolve a venv symlink to its base interpreter.
COMMAND=PYTHON.parent / ("font-coverage-plan.exe" if os.name=="nt" else "font-coverage-plan")
CASES=0
def run(args, expected=0, data=True):
    global CASES
    p=subprocess.run([str(COMMAND), *map(str,args)],cwd=WORK,text=True,capture_output=True,timeout=30)
    assert p.returncode==expected, (args,p.returncode,p.stdout,p.stderr)
    CASES+=1
    if expected==2:
        assert not p.stdout and p.stderr, (args,p.stdout,p.stderr)
        return None
    return json.loads(p.stdout) if data else p.stdout

with tempfile.TemporaryDirectory(prefix="installed-command-") as tmp:
    WORK=pathlib.Path(tmp)
    assert not WORK.is_relative_to(SOURCE)
    env=subprocess.run([str(PYTHON),"-c","import font_coverage_plan; print(font_coverage_plan.__file__)"],cwd=WORK,text=True,capture_output=True,check=True)
    installed=pathlib.Path(env.stdout.strip()).absolute()
    assert not installed.is_relative_to(SOURCE), installed
    assert installed.read_bytes()==(SOURCE/"font_coverage_plan.py").read_bytes()
    run(["--help"],data=False)
    run(["--make-example","fixture"])
    args=["--corpus","fixture/corpus.txt","fixture/latin.ttf","fixture/accent.ttf"]
    r=run(args);assert r["unique_codepoints"]==4 and not r["uncovered"] and len(r["greedy_plan"])==2
    (WORK/"fixture/corpus.txt").write_text("ABé🙂Z",encoding="utf-8")
    r=run(args,1);assert r["uncovered"]==["U+005A"]
    (WORK/"bad.ttf").write_bytes(b"badfont");run(["--corpus","fixture/corpus.txt","bad.ttf"],2)
    run(args+["fixture/latin.ttf"],2)
    run(["--make-example","fixture"],2)
    (WORK/"fixture/corpus.txt").write_bytes(b"x"*(2*1024*1024+1));run(args,2)
print(json.dumps({"installed_command":"font-coverage-plan","cases":CASES,"module_bytes_match_source":True,"outside_checkout":True,"python":subprocess.check_output([str(PYTHON),"--version"],text=True).strip()}))
