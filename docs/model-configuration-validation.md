# Configurable model validation

2026-11-06: source-only follow-up to adaptive staffing. Shipped root/director
`gpt-6-astra` and specialist `gpt-6.1-sol` pins remain unchanged. Users may edit
model IDs or omit/comment out role/root model fields. The manager respects host
resolution and reports unsupported IDs rather than silently substituting models.
See [configuration instructions](../README.md#configure-models).

The validator accepts omitted configuration models and alternate nonempty IDs;
blank, nonstring, whitespace-containing and literal `inherit` values fail. It does
not query provider availability. The optional default_subagent_model is validated
when present but is not added to shipped configuration. Pipeline participants in
both profiles must name the actual resolved execution model; config omission is
not an actual-model attribution. Alternate IDs do not relax selected independent
review, role separation, scoped hashes or editor custody.

Validation: 49 unit tests passed, including omission/alternate root and role models,
invalid values, alternate strict/adaptive participants, and selected reviewer
separation. Configuration validation passed for 15 skills and 13 roles. Changed
skills pass the skill-creator quick check. No Unreal/editor/package/gameplay rerun
was performed or needed for this source/configuration change. Historical experiment
artifacts and their recorded model identities are unchanged; their engine evidence
does not validate these later tools. Actual future model execution remains a host
observation, not something this configuration validator proves.

A separate [native configuration probe](evidence/model-resolution.json) observed
three custom-role cases from a read-only Astra parent: an explicit Sol pin ran Sol,
an edited Astra pin ran Astra, and an omitted model inherited Astra. No explicit
spawn-model override or subagent-model default was set. The probe inspected actual
session/turn_context metadata rather than self-reported identity. It is a limited
configuration-resolution check, not a model-quality or gameplay benchmark and not
a guarantee that every alternate ID is available. See [the result table](validation-results.md).
