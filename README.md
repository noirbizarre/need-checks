# Need Checks

[![CI](https://github.com/noirbizarre/need-checks/actions/workflows/ci.yml/badge.svg)](https://github.com/noirbizarre/need-checks/actions/workflows/ci.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/noirbizarre/need-checks/0.1.4.svg)](https://results.pre-commit.ci/latest/github/noirbizarre/need-checks/0.1.4)
[![codecov](https://codecov.io/gh/noirbizarre/need-checks/graph/badge.svg?token=zcMKc9CqAG)](https://codecov.io/gh/noirbizarre/need-checks)

Expect or wait status checks for a commit

## Usage

```yaml
- uses: noirbizarre/need-checks@0.1.4
  with:
    token: ${{ github.token }}
```

<!-- auto:start -->
## Inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `token` | Github token used to query Github API | `${{ github.token }}` | `false` |
| `repository` | Github repository to wait for | `${{ github.repository }}` | `false` |
| `ref` | git ref to check status on | `${{ github.sha }}` | `false` |
| `workflow` | Restrict checks to a given workflow | `""` | `false` |
| `wait` | Wait for all status check | `false` | `false` |
| `wait_interval` | time interval (in seconds) between checks while waiting | `60` | `false` |
| `wait_timeout` | max time to wait if defined | `""` | `false` |
| `conclusions` | comma separated list of accepted conclusions | `success,skipped` | `false` |

## Outputs

N/A
<!-- auto:end -->
