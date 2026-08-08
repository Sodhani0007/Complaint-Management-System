# Contributing

Thanks for considering a contribution to this project.

## Getting Started

1. Fork the repository and clone your fork
2. Follow the [backend](README.md#backend-setup) and [frontend](README.md#frontend-setup) setup
   instructions in the README
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Guidelines

- **Backend**: follow the existing layering (router → service → repository); business logic never
  belongs in a router or a LangGraph node — see `docs/architecture.md` for the reasoning
- **Frontend**: keep Redux slices scoped to a single concern (see `extractionSlice` vs.
  `complaintSlice` for why they're separate)
- Run `ruff check app` (backend) and `npx tsc -b` (frontend) before opening a PR — both run in CI
  and a failing check will block merge
- Add or update tests for any behavior change in `backend/tests/`

## Commit Messages

Use clear, present-tense messages describing what the commit does, e.g. `Add duplicate complaint
detection endpoint`, not `updates` or `fix stuff`. See `docs/GIT_WORKFLOW.md` for a worked example
of an incremental commit sequence.

## Pull Requests

- Keep PRs focused on one change; large unrelated changes are harder to review
- Describe *why* the change is needed, not just what changed
- Link any related issue

## Reporting Issues

Open a GitHub issue with steps to reproduce, expected behavior, and actual behavior. For security
issues, see [`SECURITY.md`](SECURITY.md) instead of opening a public issue.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Participation implies agreement
to its terms.
