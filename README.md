# git-monitor

A lightweight command-line tool for monitoring Git repositories across multiple project directories.

`git-monitor` recursively scans specified directories, identifies Git repositories, and reports their current branch, synchronization status with remote upstream branches, and uncommitted local changes.

## Features

- Recursively discovers Git repositories in specified directories.
- Identifies the current branch of each repository.
- Detects detached HEAD states.
- Compares local branches with their remote upstream branches.
- Identifies repositories that are ahead, behind, or have diverged from their remotes.
- Detects uncommitted local changes, including staged, unstaged, and untracked files.
- Identifies missing upstream configurations and unavailable upstream references.
- Supports scanning without fetching remote information.
- Recognizes Git repositories using either a `.git` directory or a `.git` file.
- Does not perform pull, push, merge, rebase, checkout, or reset operations.

## Requirements

- Python 3.9 or newer
- Git installed and available in `PATH`

No additional Python packages are required.

## Installation

Clone the repository:

```bash
git clone git@github.com:Roeh0/git-monitor.git
```

Navigate to the project directory:

```bash
cd git-monitor
```

## Usage

Run the tool by providing one or more directories to scan:

```bash
python git_monitor.py ~/Projects/Core ~/Projects/External
```

### Available options

**Skip remote fetching**

```bash
python git_monitor.py --no-fetch ~/Projects/Core ~/Projects/External
```

By default, `git-monitor` fetches remote information before comparing repository states. It also prunes outdated remote-tracking references.

The `--no-fetch` option skips fetching and uses locally cached remote-tracking references instead. Results may therefore be outdated.

## Report

Each discovered repository is reported with three fields:

| Field | Description |
|---|---|
| `Branch` | Current branch name, `DETACHED HEAD`, or `UNKNOWN`. |
| `Remote` | Synchronization status with the configured upstream branch. |
| `Local` | Status of the working tree and staging area. |

## Statuses

### Branch

| Value | Description |
|---|---|
| Branch name | The currently checked-out local branch. |
| `DETACHED HEAD` | HEAD points directly to a commit rather than a local branch. |
| `UNKNOWN` | The current branch could not be determined. |

### Remote status

| Status | Description |
|---|---|
| `UP TO DATE` | Local branch matches its remote upstream. |
| `UPDATE AVAILABLE` | Remote branch contains commits not present locally. |
| `PUSH NEEDED` | Local branch contains commits not present remotely. |
| `DIVERGED` | Local and remote branches contain different commits. |
| `NO UPSTREAM` | No upstream branch is configured for the current branch. |
| `UPSTREAM MISSING` | The configured upstream reference is not available locally. |
| `FETCH FAILED` | Remote information could not be fetched. |
| `NO BRANCH` | Repository is in a detached HEAD state. |
| `UNKNOWN` | Remote status could not be determined. |

### Local status

| Status | Description |
|---|---|
| `CLEAN` | No uncommitted changes detected. |
| `LOCAL CHANGES` | Staged, unstaged, or untracked changes detected. |
| `UNKNOWN` | Local repository status could not be determined. |

## Safety

`git-monitor` is designed to inspect repositories without modifying their working files, local commits, or current branches.

When remote fetching is enabled, Git updates remote-tracking references and related metadata inside the `.git` directory. The `--prune` option also removes outdated remote-tracking references.

The tool does not automatically merge, rebase, pull, push, checkout, or reset repositories.
