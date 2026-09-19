"""Install and exercise the fixed V2 lifecycle in a NEW synthetic local project."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from seed import ROOT, install, load


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=Path)
    a = p.parse_args()
    target = a.target or Path(tempfile.mkdtemp(prefix="fixed-v2-verification-")) / "project"
    _, payload, receipt = load()
    install(target, payload, receipt)
    target = target.absolute()
    if (target / "product.py").exists() or (target / ".harness").exists():
        raise ValueError("demo requires a fresh project; existing sources are preserved")
    (target / "product.py").write_text("def total(a, b):\n    return a + b\n", encoding="utf-8")
    (target / "test_product.py").write_text("import runpy\np = runpy.run_path('product.py')\nassert p['total'](2, 3) == 5\nprint('sum user flow: passed')\n", encoding="utf-8")
    setup = json.loads((ROOT / "seed/docs/harness/examples/setup.example.json").read_text(encoding="utf-8"))
    results = []
    def call(command, body, actor="owner"):
        key = f"demo-{len(results)+1:02}"
        data = target / "requests" / (key + ".json")
        data.parent.mkdir(exist_ok=True)
        data.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        proc = subprocess.run([sys.executable, "-B", str(target / "harness.py"), "--root", str(target), command, "--data", str(data), "--actor", actor, "--key", key], capture_output=True, text=True, encoding="utf-8")
        if proc.returncode:
            raise RuntimeError(proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        if result.get("projection_warning"):
            raise RuntimeError(result)
        results.append({"command": command, "result": result})
        return result
    call("init", setup)
    call("object", {"id": "REQ-SUM", "type": "Requirement", "title": "합계 계산", "purpose": "두 수를 입력하면 합계를 반환한다", "sources": ["product.py"], "relations": []})
    call("object", {"id": "MODULE-SUM", "type": "Module", "title": "합계 모듈", "purpose": "기본 사용자 흐름의 구현", "sources": ["product.py"], "relations": ["REQ-SUM"]})
    def task(name):
        return call("task", {"id": name, "requirement": "REQ-SUM", "purpose": "합계 흐름 구현과 테스트", "authority_ref": "synthetic local demo only", "acceptance": "mixed"})
    task("TASK-BASE")
    run = call("run", {"task": "TASK-BASE"})
    assert run["state"] == "passed"
    call("resume", {"run": run["id"]})
    call("mvp", {"run": run["id"], "user_flow": "synthetic 2+3=5", "decision_ref": "synthetic owner acceptance; not a real product decision"})
    call("observe", {"id": "OBS-NEXT", "task": "TASK-BASE", "category": "expression_preference", "summary": "다음 진행 명령을 현재 권한 내 작업 한 건으로 해석", "evidence_ref": "synthetic command fixture", "suggestion": {"aliases": {"다음 진행": "next_ready"}, "output_format": "compact"}})
    cid = call("checkpoint", {})["candidates"][0]
    task("TASK-IN-FLIGHT")
    ev = call("evaluate", {"candidate": cid}, "evaluator")
    assert ev["passed"]
    call("adopt", {"candidate": cid, "decision_ref": "synthetic local scoped approval"})
    task("TASK-V3")
    resolutions = {}
    for name in ("TASK-IN-FLIGHT", "TASK-V3"):
        proc = subprocess.run([sys.executable, "-B", str(target / "harness.py"), "--root", str(target), "resolve", "--task", name, "--command", "다음 진행"], capture_output=True, text=True, encoding="utf-8", check=True)
        resolutions[name] = json.loads(proc.stdout)
    assert resolutions["TASK-IN-FLIGHT"]["action"] == "clarify"
    assert resolutions["TASK-V3"]["tasks"] == ["TASK-V3"]
    v3_run = call("run", {"task": "TASK-V3"})
    assert v3_run["state"] == "passed" and v3_run["config_id"].startswith("V3-")
    call("resume", {"run": v3_run["id"]})
    call("mvp", {"run": v3_run["id"], "user_flow": "same synthetic sum flow under frozen V3", "decision_ref": "synthetic owner decision only"})
    report = {"project": str(target), "wiki": str(target / "wiki/index.html"), "synthetic_only": True, "live_llm_calls": 0, "operations": results, "resolutions": resolutions}
    (target / "demo-evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"project": str(target), "wiki": report["wiki"], "operations": len(results), "eval_passed": ev["passed"], "actual_llm_quality": "unverified"}, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
