
import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Repository:
    path: Path
    branch: str
    remote_status: str
    local_status: str


def run_git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"

    try:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(
            args, 1, stdout="", stderr="Git command failed"
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="git-monitor",
        description="Monitor Git repositories across multiple directories.",
    )
    parser.add_argument(
        "directories",
        metavar="DIRECTORY",
        nargs="+",
        type=Path,
        help="directories to scan",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="skip fetching and use locally cached remote information",
    )

    args = parser.parse_args()
    directories = []

    for directory in args.directories:
        directory = directory.expanduser()

        if not directory.is_dir():
            parser.error(f"Not a valid directory: {directory}")

        directory = directory.resolve()

        if directory not in directories:
            directories.append(directory)

    args.directories = directories
    return args


def discover_repositories(directories: list[Path]) -> list[Path]:
    repositories = set()

    def handle_error(error: OSError) -> None:
        print(f"Warning: Cannot access {error.filename}", file=sys.stderr)

    for directory in directories:
        for root, dirs, files in os.walk(
            directory,
            topdown=True,
            onerror=handle_error,
            followlinks=False,
        ):
            if ".git" in dirs or ".git" in files:
                repositories.add(Path(root).resolve())
                dirs[:] = [name for name in dirs if name != ".git"]

    return sorted(repositories)


def inspect_repository(path: Path, fetch: bool = True) -> Repository:
    branch_result = run_git(path, "branch", "--show-current")

    if branch_result.returncode != 0:
        return Repository(path, "UNKNOWN", "UNKNOWN", "UNKNOWN")

    branch = branch_result.stdout.strip() or "DETACHED HEAD"

    status_result = run_git(
        path,
        "status",
        "--porcelain",
        "--untracked-files=normal",
    )

    if status_result.returncode != 0:
        local_status = "UNKNOWN"
    elif status_result.stdout.strip():
        local_status = "LOCAL CHANGES"
    else:
        local_status = "CLEAN"

    if branch == "DETACHED HEAD":
        return Repository(path, branch, "NO BRANCH", local_status)

    upstream_result = run_git(
    path,
    "rev-parse",
    "--symbolic-full-name",
    "@{upstream}",
    )

    if upstream_result.returncode != 0:
        return Repository(path, branch, "NO UPSTREAM", local_status)

    upstream = upstream_result.stdout.strip()

    if fetch:
        fetch_result = run_git(
            path,
            "fetch",
            "--prune",
            "--quiet",
            "--no-recurse-submodules",
        )

        if fetch_result.returncode != 0:
            return Repository(path, branch, "FETCH FAILED", local_status)

    upstream_check = run_git(
        path,
        "show-ref",
        "--verify",
        "--quiet",
        upstream,
    )

    if upstream_check.returncode != 0:
        return Repository(path, branch, "UPSTREAM MISSING", local_status)

    comparison = run_git(
        path,
        "rev-list",
        "--left-right",
        "--count",
        f"HEAD...{upstream}",
    )

    if comparison.returncode != 0:
        remote_status = "UNKNOWN"
    else:
        try:
            ahead, behind = map(int, comparison.stdout.split())

            if ahead and behind:
                remote_status = "DIVERGED"
            elif behind:
                remote_status = "UPDATE AVAILABLE"
            elif ahead:
                remote_status = "PUSH NEEDED"
            else:
                remote_status = "UP TO DATE"

        except ValueError:
            remote_status = "UNKNOWN"

    return Repository(path, branch, remote_status, local_status)


def display_report(repositories: list[Repository]) -> None:
    print("\ngit-monitor")
    print("=" * 64)

    if not repositories:
        print("No Git repositories found.")
        return

    for repository in repositories:
        print(f"\n{repository.path}")
        print(f"  Branch:  {repository.branch}")
        print(f"  Remote:  {repository.remote_status}")
        print(f"  Local:   {repository.local_status}")

    print("\n" + "=" * 64)
    print(f"Repositories checked: {len(repositories)}")
    print("=" * 64)


def main() -> int:
    args = parse_arguments()

    paths = discover_repositories(args.directories)
    repositories = [
        inspect_repository(path, fetch=not args.no_fetch)
        for path in paths
    ]

    display_report(repositories)
    return 0


if __name__ == "__main__":
    sys.exit(main())
