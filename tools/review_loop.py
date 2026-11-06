#!/usr/bin/env python3
"""Record a real agent handoff and gate completion on current review + evidence.

This is an evidence-consistency tool, not an agent launcher or identity verifier.
The coordinator must actually use the host's subagent tools and record returned IDs.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value.strip()


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("Unsupported journal schema")
    return data


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            name = stream.name
            json.dump(data, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()


def event(data, kind, actor, **details):
    data["events"].append({"sequence": len(data["events"]) + 1, "utc": utc(),
                           "kind": kind, "actor": actor, **details})


def safe_path(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts or str(path) == ".":
        raise ValueError("Scopes must be explicit relative paths inside the source root")
    target = root / path
    if not target.resolve().is_relative_to(root):
        raise ValueError("Scope escapes source root")
    for parent in [target, *target.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("Symlinks are not supported in review scopes")
    return target


def snapshot(data):
    root = Path(data["root"])
    files = {}
    for scope in data["scopes"]:
        target = safe_path(root, scope)
        entries = sorted(target.rglob("*")) if target.is_dir() else [target]
        for entry in entries:
            relative = entry.relative_to(root).as_posix()
            safe_path(root, relative)
            if entry.is_dir():
                continue
            files[relative] = sha(entry) if entry.is_file() else None
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"files": files, "digest": digest}


def initialize(path, root, implementer, reviewer, coordinator, scopes, criteria,
               required_checks, max_repairs=3):
    path = Path(path).resolve()
    if path.exists():
        raise ValueError("Journal already exists; preserve the previous run")
    root = Path(root).resolve(strict=True)
    people = {k: nonempty(v, k) for k, v in dict(implementer=implementer,
              reviewer=reviewer, coordinator=coordinator).items()}
    if len({v.casefold() for v in people.values()}) != 3:
        raise ValueError("Coordinator, implementer and independent reviewer must be distinct")
    if not scopes or not criteria or not required_checks:
        raise ValueError("At least one scope, criterion and required check are needed")
    if not isinstance(max_repairs, int) or not 0 <= max_repairs <= 20:
        raise ValueError("max_repairs must be between 0 and 20")
    normalized = []
    for scope in scopes:
        target = safe_path(root, scope)
        if not target.exists():
            raise ValueError(f"Create the source scope before initializing: {scope}")
        if target == path or (target.is_dir() and path.is_relative_to(target)):
            raise ValueError("Keep the journal outside its source scopes")
        normalized.append(target.relative_to(root).as_posix())
    data = {"schema": 1, "root": str(root), "participants": people,
            "scopes": sorted(set(normalized)),
            "criteria": [nonempty(c, "criterion") for c in criteria],
            "required_checks": sorted({nonempty(c, "check") for c in required_checks}),
            "max_repairs": max_repairs, "rounds": [], "events": []}
    event(data, "initialized", coordinator)
    save(path, data)
    return data


def require_actor(data, actor, roles):
    if actor not in [data["participants"][role] for role in roles]:
        raise ValueError("Actor is not the recorded " + " or ".join(roles))


def current_round(data):
    if not data["rounds"]:
        raise ValueError("Submit an implementation first")
    return data["rounds"][-1]


def require_current(data):
    current = current_round(data)
    if snapshot(data)["digest"] != current["snapshot"]["digest"]:
        raise ValueError("Source changed after submission; submit and review the new snapshot")
    return current


def submit(path, actor, summary, addressed=(), supersede_pending=False):
    data = load(path)
    require_actor(data, actor, ["implementer"])
    summary = nonempty(summary, "implementation summary")
    addressed = sorted({nonempty(x, "finding ID") for x in addressed})
    next_snapshot = snapshot(data)
    superseded = None
    if data["rounds"]:
        previous = current_round(data)
        if len(data["rounds"]) > data["max_repairs"]:
            raise ValueError("Repair limit reached; report unresolved work instead of passing")
        if previous["review"] is None:
            if not supersede_pending:
                raise ValueError("Pending review: finish it, or use --supersede-pending if source changed")
            if previous["snapshot"]["digest"] == next_snapshot["digest"]:
                raise ValueError("Only a stale pending review can be superseded")
            superseded = previous["number"]
            expected = set()
        else:
            if supersede_pending:
                raise ValueError("The previous round already has a review; submit its repairs normally")
            expected = {f["id"] for f in previous["review"]["findings"]}
        if set(addressed) != expected:
            raise ValueError("Resubmission must address every previous finding ID, and no invented IDs")
    elif addressed or supersede_pending:
        raise ValueError("Initial submission has no findings or pending review to supersede")
    item = {"number": len(data["rounds"]) + 1, "snapshot": next_snapshot,
            "implementation": {"actor": actor, "summary": summary, "addressed": addressed},
            "review": None, "verification": {}}
    data["rounds"].append(item)
    if superseded is not None:
        event(data, "pending_review_superseded", actor, round=superseded,
              replacement_round=item["number"], reason=summary)
    event(data, "implementation_submitted", actor, round=item["number"],
          digest=item["snapshot"]["digest"], addressed=addressed)
    save(path, data)
    return item


def review(path, actor, report):
    data = load(path)
    require_actor(data, actor, ["reviewer"])
    current = require_current(data)
    if current["review"] is not None:
        raise ValueError("Review already recorded; submit another revision instead of overwriting it")
    if report.get("digest") != current["snapshot"]["digest"]:
        raise ValueError("Review must identify the exact submitted digest")
    verdict = report.get("verdict")
    findings = report.get("findings")
    if verdict not in ("approve", "request_changes") or not isinstance(findings, list):
        raise ValueError("Review requires verdict approve/request_changes and a findings list")
    nonempty(report.get("summary"), "review summary")
    ids = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("Each finding must be an object")
        for field in ("id", "severity", "location", "trigger", "consequence", "evidence"):
            nonempty(finding.get(field), "finding " + field)
        if finding["id"] in ids or finding["severity"] not in ("P0", "P1", "P2", "P3"):
            raise ValueError("Findings need unique IDs and severity P0-P3")
        ids.add(finding["id"])
    if (verdict == "approve") != (len(findings) == 0):
        raise ValueError("Approval requires no unresolved findings; request_changes needs a finding")
    current["review"] = {"actor": actor, "utc": utc(), "digest": report["digest"],
                         "verdict": verdict, "summary": report["summary"], "findings": findings}
    event(data, "review_completed", actor, round=current["number"], verdict=verdict, finding_ids=sorted(ids))
    save(path, data)
    return current["review"]


def verify(path, actor, check, status, evidence, summary):
    data = load(path)
    require_actor(data, actor, ["coordinator", "reviewer"])
    current = require_current(data)
    if check not in data["required_checks"]:
        raise ValueError("Check is not one of the declared required checks")
    if status not in ("passed", "failed", "not_run"):
        raise ValueError("Verification status must be passed, failed or not_run")
    nonempty(summary, "verification summary")
    artifact = Path(evidence).resolve(strict=True)
    if not artifact.is_file() or artifact == Path(path).resolve():
        raise ValueError("Evidence must be a separate regular file")
    value = {"actor": actor, "status": status, "summary": summary,
             "source_digest": current["snapshot"]["digest"],
             "evidence": str(artifact), "sha256": sha(artifact), "utc": utc()}
    current["verification"][check] = value
    event(data, "verification_recorded", actor, round=current["number"], check=check,
          result=value)
    save(path, data)
    return value


def status(path):
    data = load(path)
    result = {"ready": False, "state": "awaiting_implementation", "reasons": [],
              "participants": data["participants"], "round": len(data["rounds"])}
    if not data["rounds"]:
        return result
    current = current_round(data)
    result["digest"] = current["snapshot"]["digest"]
    if snapshot(data)["digest"] != result["digest"]:
        result.update(state="stale", reasons=["Source bytes or scoped file inventory changed"])
        if current["review"] is None:
            result["recovery"] = "submit --supersede-pending; requires fresh review and verification"
        return result
    report = current["review"]
    if report is None:
        result["state"] = "awaiting_review"
        return result
    if report["verdict"] != "approve":
        result.update(state="changes_requested", reasons=[f["id"] for f in report["findings"]])
        if len(data["rounds"]) > data["max_repairs"]:
            result["state"] = "repair_limit_reached"
        return result
    for check in data["required_checks"]:
        record = current["verification"].get(check)
        if not record or record["status"] != "passed":
            result["reasons"].append(check + ": " + (record["status"] if record else "not_run"))
        elif record["source_digest"] != result["digest"]:
            result["reasons"].append(check + ": stale source")
        elif not Path(record["evidence"]).is_file() or sha(record["evidence"]) != record["sha256"]:
            result["reasons"].append(check + ": evidence changed or missing")
    result["ready"] = not result["reasons"]
    result["state"] = "complete" if result["ready"] else "awaiting_verification"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Declare real participant IDs, source scopes and acceptance criteria")
    init.add_argument("--root", required=True)
    for key in ("implementer", "reviewer", "coordinator"):
        init.add_argument("--" + key, required=True)
    for name in ("scope", "criterion", "require-check"):
        init.add_argument("--" + name, action="append", required=True)
    init.add_argument("--max-repairs", type=int, default=3)
    sub = commands.add_parser("submit", help="Freeze a source snapshot; resubmit after fixing review findings")
    sub.add_argument("--summary", required=True)
    sub.add_argument("--addressed", action="append", default=[])
    sub.add_argument("--supersede-pending", action="store_true",
                     help="Replace a stale pending-review round, preserving it and consuming one repair cycle")
    rev = commands.add_parser("review", help="Record the independent review JSON for the exact digest")
    rev.add_argument("--report", required=True)
    ver = commands.add_parser("verify", help="Record an observed result and hash its evidence file")
    ver.add_argument("--check", required=True)
    ver.add_argument("--status", choices=["passed", "failed", "not_run"], required=True)
    ver.add_argument("--evidence", required=True)
    ver.add_argument("--summary", required=True)
    for command in (init, sub, rev, ver):
        command.add_argument("--journal", required=True)
    for command in (sub, rev, ver):
        command.add_argument("--actor", required=True)
    for name in ("status", "gate"):
        commands.add_parser(name, help="Inspect readiness" if name == "status" else "Exit 1 unless review and checks are current and passed").add_argument("--journal", required=True)
    a = parser.parse_args(argv)
    try:
        if a.command == "init":
            result = initialize(a.journal, a.root, a.implementer, a.reviewer, a.coordinator,
                                a.scope, a.criterion, a.require_check, a.max_repairs)
        elif a.command == "submit":
            result = submit(a.journal, a.actor, a.summary, a.addressed, a.supersede_pending)
        elif a.command == "review":
            result = review(a.journal, a.actor, json.loads(Path(a.report).read_text(encoding="utf-8-sig")))
        elif a.command == "verify":
            result = verify(a.journal, a.actor, a.check, a.status, a.evidence, a.summary)
        else:
            result = status(a.journal)
        print(json.dumps(result, indent=2))
        return int(a.command == "gate" and not result["ready"])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
