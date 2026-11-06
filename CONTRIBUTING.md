# Contributing

## Documentation language

English is the canonical language for documentation, skills, roles, and CLI text.
Korean is the only additional documentation language currently maintained.
The Korean README lives at docs/readme/README_ko.md; other Korean translations
live under docs/ko. Add reciprocal English/Korean links to translated documents.
When updating a translated page, keep its Korean version in sync, including
commands, validation scope, and limitations. Preserve technical identifiers and
adjust relative links for the translation's location.

## Development

Keep workflows small and grounded in an actual Unreal task. Preserve user model,
sandbox and authorization choices. Runtime scripts use Python 3.11+ standard
library; development validation uses requirements-dev.txt.

Run `python tools/validate.py` and `python -m unittest discover -s tests -v`.
Changes to MCP behavior also need a disposable-project live test with engine
version and outcomes recorded. CI does not run Unreal Engine.

Do not commit Epic source, engine binaries, generated .uasset/.umap fixtures,
credentials, personal project paths or huge runtime traces. Report experimental
API differences with minimal reproduction, not copied engine source files.

Open issues/PRs with the trigger, expected/observed behavior, engine/Codex versions
and the validation actually performed. Do not claim that every specialist or
toolset has been tested because configuration parsing passed.
