# Need Checks

[![CI](https://github.com/noirbizarre/need-checks/actions/workflows/ci.yml/badge.svg)](https://github.com/noirbizarre/need-checks/actions/workflows/ci.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/noirbizarre/need-checks/main.svg)](https://results.pre-commit.ci/latest/github/noirbizarre/need-checks/main)
[![codecov](https://codecov.io/gh/noirbizarre/need-checks/graph/badge.svg?token=zcMKc9CqAG)](https://codecov.io/gh/noirbizarre/need-checks)

Expect or wait status checks for a commit

## Usage

```yaml
- uses: noirbizarre/need-checks@main
  with:
    token: ${{ github.token }}
```

## Permissions

This action uses the GitHub token to query GitHut API and requires the following permissions:
```yaml
actions: read
checks: read
contents: read
```

<!-- auto:start -->
## Inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `token` | GitHub token with proper permissions to query the API | `${{ github.token }}` | `false` |
| `repository` | GitHub repository to wait for | `${{ github.repository }}` | `false` |
| `ref` | git ref to check status on | `${{ github.ref }}` | `false` |
| `workflow` | Restrict checks to a given workflow | `""` | `false` |
| `wait` | Wait for all status check | `false` | `false` |
| `wait_interval` | time interval (in seconds) between checks while waiting | `60` | `false` |
| `wait_timeout` | max time to wait if defined | `""` | `false` |
| `conclusions` | comma separated list of accepted conclusions | `success,skipped` | `false` |

## Outputs

N/A
<!-- auto:end -->
