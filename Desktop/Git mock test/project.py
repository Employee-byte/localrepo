
import argparse
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "issues.json"
PRIORITIES = ["high", "medium", "low"]
STATUSES = ["open", "in_progress", "closed"]
TITLE_LENGTH = 30


def load_issues():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            issues = json.load(file)
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Cannot read issues.json: {exc}")

    if not isinstance(issues, list):
        raise SystemExit("issues.json must contain a list of issues.")

    return issues


def save_issues(issues):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(issues, file, indent=2)


def find_issue(issues, issue_id):
    for issue in issues:
        if issue["id"] == issue_id:
            return issue
    return None


def create_issue(args):
    issues = load_issues()
    next_id = max((item["id"] for item in issues), default=0) + 1

    issue = {
        "id": next_id,
        "title": args.title,
        "priority": args.priority,
        "status": "open",
    }

    issues.append(issue)
    save_issues(issues)
    print(f"Created issue #{next_id}: {issue['title']}")


def get_issue(args):
    issue = find_issue(load_issues(), args.issue_id)

    if issue is None:
        print(f"Issue #{args.issue_id} not found.")
        return

    print(json.dumps(issue, indent=2))


def list_issues(args):
    issues = load_issues()

    if not issues:
        print("No issues found.")
        return

    for issue in issues:
        print(
            f"#{issue['id']} | {issue['status']} | "
            f"{issue['priority']} | {issue['title']}"
        )


def update_issue(args):
    issues = load_issues()
    issue = find_issue(issues, args.issue_id)

    if issue is None:
        print(f"Issue #{args.issue_id} not found.")
        return

    if args.title is None and args.priority is None and args.status is None:
        print("Provide at least one field to update.")
        return

    if args.title is not None:
        issue["title"] = args.title
    if args.priority is not None:
        issue["priority"] = args.priority
    if args.status is not None:
        issue["status"] = args.status

    save_issues(issues)
    print(f"Updated issue #{args.issue_id}.")


def delete_issue(args):
    issues = load_issues()
    issue = find_issue(issues, args.issue_id)

    if issue is None:
        print(f"Issue #{args.issue_id} not found.")
        return

    issues.remove(issue)
    save_issues(issues)
    print(f"Deleted issue #{args.issue_id}.")


def triage_issues(args):
    issues = load_issues()
    priority_order = {name: index for index, name in enumerate(PRIORITIES)}

    open_issues = [item for item in issues if item["status"] == "open"]
    open_issues.sort(
        key=lambda item: (
            priority_order.get(item["priority"], len(PRIORITIES)),
            item["id"],
        )
    )

    for issue in open_issues[:args.limit]:
        print(
            f"#{issue['id']} | {issue['priority']} | {issue['title']}"
        )

    if not open_issues:
        print("No open issues to triage.")


def issue_ref(args):
    issue = find_issue(load_issues(), args.issue_id)

    if issue is None:
        print(f"Issue #{args.issue_id} not found.")
        return

    title = issue["title"]
    if len(title) > TITLE_LENGTH:
        title = title[:TITLE_LENGTH - 3] + "..."

    print(f"#{issue['id']}: {title}")


def consolidate_windows(args):
    intervals = []

    for value in args.intervals:
        try:
            start_text, end_text = value.split(":")
            start, end = int(start_text), int(end_text)
        except ValueError:
            raise SystemExit(
                f"Invalid interval '{value}'. Use START:END, e.g. 1:3."
            )

        if start > end:
            raise SystemExit(f"Invalid interval '{value}': start > end.")

        intervals.append((start, end))

    intervals.sort()
    merged = []

    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    print(" ".join(f"{start}:{end}" for start, end in merged))


def build_parser():
    parser = argparse.ArgumentParser(description="Python Issue Tracker")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Create an issue")
    create.add_argument("--title", required=True)
    create.add_argument("--priority", choices=PRIORITIES, default="medium")
    create.set_defaults(func=create_issue)

    get = commands.add_parser("get", help="Show one issue")
    get.add_argument("issue_id", type=int)
    get.set_defaults(func=get_issue)

    listing = commands.add_parser("list", help="List all issues")
    listing.set_defaults(func=list_issues)

    update = commands.add_parser("update", help="Update an issue")
    update.add_argument("issue_id", type=int)
    update.add_argument("--title")
    update.add_argument("--priority", choices=PRIORITIES)
    update.add_argument("--status", choices=STATUSES)
    update.set_defaults(func=update_issue)

    delete = commands.add_parser("delete", help="Delete an issue")
    delete.add_argument("issue_id", type=int)
    delete.set_defaults(func=delete_issue)

    triage = commands.add_parser("triage", help="Rank open issues")
    triage.add_argument("--limit", type=int, default=5)
    triage.set_defaults(func=triage_issues)

    ref = commands.add_parser("ref", help="Show a truncated title")
    ref.add_argument("issue_id", type=int)
    ref.set_defaults(func=issue_ref)

    windows = commands.add_parser("windows", help="Merge overlapping windows")
    windows.add_argument("intervals", nargs="+")
    windows.set_defaults(func=consolidate_windows)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "triage" and args.limit < 0:
        parser.error("--limit must be zero or greater")

    args.func(args)


if __name__ == "__main__":
    main()
