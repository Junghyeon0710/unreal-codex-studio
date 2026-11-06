# Adaptive Astra management

The Astra manager (`gpt-6-astra`) chooses the smallest sufficient team for the
actual task. Selected specialists default to `gpt-6.1-sol`. A role catalog is not a
fixed roster. Decide roles, count, scopes, dependencies and meaningful checks from
the request, risk and available tools; add or reassign specialists when findings
justify it. Do not ask the user to choose routine staffing. Preserve explicit user
choices, authorization, sandbox and approval policy. Config defaults do not change
an existing root chat's model.

A short explanation may need only the manager or one researcher and no journal.
A material change may need one editor specialist. A code defect may warrant a code
author and independent reviewer. A larger feature may need editor, build and QA
specialists. These are examples, not fixed templates. Independent review is used
when useful, requested or claimed; if selected, the reviewer must differ from the
author and must inspect the actual changes. Build, package and gameplay QA work
belongs in the plan only when it meaningfully verifies the task.

## Management and ownership

1. Define the requested outcome and observable acceptance. Select useful roles and
   assign explicit scopes, dependencies and checks. Answer directly when delegation
   or a tracking tool would add no value.
2. When delegating, use actual host calls and record returned IDs/model attribution
   if recording a run. Role files, names and journals do not launch agents. Never
   invent a worker or claim independent review performed by its own author.
3. Let each selected worker perform its assigned scope. Route findings back to the
   responsible author and obtain renewed review when that review is part of the
   plan. Bound repair work (three cycles by default for tracked tasks); unresolved
   findings remain explicit. Do not manufacture defects or unnecessary checks.
4. If editor operations are needed, designate one actual owner for all official MCP
   calls, including reads, binary asset edits and PIE state. Bind the exact project
   with doctor, discover live schemas, and release custody before other signoffs.
   Do not hand-edit binary assets or substitute ad hoc editor Python. Source-only
   or explanation work does not require an editor specialist.
5. Collect evidence for the selected checks, report actual outcomes and limits,
   and revise the plan when findings change scope or staffing. Preserve the reason,
   previous acceptance and failed/unrun outcomes; removing a check is a visible
   acceptance change, not a retroactive pass. Do not widen user scope to justify it.

A worker may cover compatible tasks when this does not undermine selected
independence or exclusive editor ownership. Independent source scopes may run in
parallel; dependent work follows its actual prerequisites. Preparation may happen
before signoff. Missing tools/delegation are limitations, not imaginary passes.

## Optional adaptive evidence journal

For work that benefits from tracked handoffs, `tools/studio_pipeline.py` defaults to
an adaptive plan. It checks evidence consistency, not identities, model authenticity,
semantic correctness or whether a test really ran. The manager is the single journal
writer. Ordinary explanations and read-only answers do not require this tool.

`participants.json` maps only actually selected roles to `{id, model}`. It includes
`coordinator` and at least one launched worker; arbitrary role names such as
`material-artist` are supported. Reserved `reviewer` selects independent snapshot
review. The plan's `author` identifies the responsible worker, not necessarily a
programmer. For an optional review-only journal, coordinator + reviewer is valid:
the coordinator submits an existing-content baseline without claiming authorship
of that content. Such review can also be done without a journal. One expert can own several compatible selected stages. An empty stage
list is allowed for a scoped task whose outcome needs no extra executable checks;
it does not imply tests or independent review passed.

For example, a source-only gate change may select code author and independent
reviewer with a meaningful test stage, without editor, package or gameplay QA:

```json
{
  "author": "code",
  "stages": [
    {"name": "source-tests", "owner": "code", "depends_on": [],
     "checks": ["unit-tests", "configuration-validator"]}
  ]
}
```

```sh
python tools/studio_pipeline.py --journal .studio/task.json init --participants .studio/participants.json --plan .studio/plan.json --root . --scope tools --scope tests --criterion "Selected stages gate current evidence"
python tools/studio_pipeline.py --journal .studio/task.json submit --actor ACTUAL_AUTHOR_ID --summary "Freeze task snapshot"
# Only if an actual independent reviewer was selected:
python tools/studio_pipeline.py --journal .studio/task.json review --actor ACTUAL_REVIEWER_ID --report .studio/review.json
python tools/studio_pipeline.py --journal .studio/task.json record --actor ACTUAL_STAGE_OWNER_ID --stage source-tests --status passed --checks .studio/checks.json --evidence .studio/test-report.json --summary "Observed selected checks" --digest SUBMITTED_DIGEST
python tools/studio_pipeline.py --journal .studio/task.json gate
```

The check JSON maps **every** selected check to `passed`, `failed` or `not_run`.
A passing stage requires all selected checks passed. Unselected stages are rejected;
selected missing stages keep the gate closed. Each stage names preceding dependencies
in `depends_on`. An upstream rerun invalidates dependent signoffs and requires newer
evidence; independent branches remain valid. Every evidence file is hashed, must
postdate the frozen snapshot and relevant upstream signoff, and must stay unchanged.

A stage with `uses_editor: true` requires custody held by that selected owner:
`custody --actor ACTUAL_EDITOR_ID --operation acquire`, then `release`. All selected
editor stages must have one actual owner. Custody may begin before a final asset
snapshot exists. For asset changes, do the work under custody, release, freeze the
final scoped content, then reacquire to record the editor report and release again.
A manager may submit the baseline/final snapshot under its own ID; this is snapshot
attribution, not a claim that the manager performed specialist work.

Change the plan with `plan --actor ACTUAL_MANAGER_ID --participants ... --plan ...
--reason "Why staffing or acceptance changed"` and optional `--scope`/`--criterion`.
History retains every version, selected participant, scope, stage and criterion.
The gate closes until a fresh snapshot and selected signoffs are recorded. Outstanding
review finding IDs still need addressed responses; a plan change does not erase them.
Plan resubmissions share the bounded repair budget. Keep journals/evidence outside
source scopes, exclude generated files, and scope all relevant inputs/configuration.
Files omitted from scopes cannot be protected by the gate.

A selected reviewer returns `digest`, `verdict` (`approve`/`request_changes`),
`summary`, and `findings`. Findings contain `id`, `severity` P0–P3, `location`,
`trigger`, `consequence`, `evidence`. Repairs use `submit --addressed FINDING_ID` and
get a fresh review. Changed source/content invalidates all snapshot signoffs.
`status` is read-only; `gate` exits 0 for complete, 1 for incomplete and 2 for invalid
inputs. A gate pass covers only the selected acceptance and recorded evidence.

## Historical and opt-in profiles

Existing schema-1 five-worker journals remain readable without changes; their
missing profile marker means the historical strict-five behavior. To deliberately
run that integration profile again, use `init --profile strict-five` with all five
specialists and the original editor/verification/QA sequence. Its `record` commands
use aggregate evidence and do not need adaptive `--checks`. It is an **opt-in test
profile**, not ordinary task staffing. `review_loop.py` remains a separate optional
two-worker implement/review utility with its own contract.

The [completed door experiment](studio-door-validation.md) records a real five-worker
run against an earlier frozen snapshot. Its old 35-test result and gate are
historical snapshot evidence; they do not validate later adaptive-tool changes.
