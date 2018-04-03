#!/usr/bin/env python3
# coding: utf-8
import argparse
import csv
import re
from datetime import (
    datetime,
)
from itertools import (
    chain,
)
from os import (
    path,
)
from typing import (
    Iterator,
    List,
    NamedTuple,
    Tuple,
    TypeVar,
)

from git import (
    Repo,
)


class LogEntry(NamedTuple):
    """
    Represents a log entry that will later be output in the CSV file
    """

    title: str
    author: str
    duration: float
    end_date: datetime
    repo: str

    def patch(self, **kwargs) -> 'LogEntry':
        d = dict(zip(self._fields, self))
        d.update(kwargs)
        return LogEntry(**d)


T = TypeVar('T')


def n_grams(it: Iterator[T], n: int) -> Iterator[Tuple[T, ...]]:
    """
    Generates n-grams, by example for n = 2

    >>> assert list(n_grams([1, 2, 3, 4], 2)) == [(1, 2), (2, 3), (3, 4)]
    """

    stack = []

    for i in it:
        stack.append(i)

        if len(stack) > n:
            stack.pop(0)

        if len(stack) == n:
            yield tuple(stack)


def parse_args() -> argparse.Namespace:
    """
    Configures and runs the arguments parser
    """

    parser = argparse.ArgumentParser(
        description='Analyzes Git repositories in order to generate a time '
                    'sheet'
    )

    parser.add_argument('repos', nargs='+', help='Paths to repositories')
    parser.add_argument(
        '--start-up-time',
        type=float,
        default=(3600 * 3),
        help='How long does it take to produce the first '
             'commit of the day? (in seconds, default is 3h)',
    )
    parser.add_argument('--author', help='Author to keep', required=True)
    parser.add_argument(
        '--title-exp',
        help='Regular expression to filter the title. It will keep only the '
             'first group.',
    )
    parser.add_argument('--output', '-o', help='Output file', required=True)

    return parser.parse_args()


def extract_logs(repo_path, duration: float) -> Iterator[LogEntry]:
    """
    Creates the initial LogEntry items for each commit found in the given repo
    (from all existing heads).

    The duration will default to the provided duration value.
    """

    visited = set()
    repo = Repo(repo_path)

    for branch in repo.references:
        for commit in repo.iter_commits(branch):
            if commit not in visited:
                yield LogEntry(
                    title=commit.message,
                    author=commit.author.name,
                    duration=duration,
                    end_date=commit.authored_datetime,
                    repo=path.basename(repo_path),
                )
                visited.add(commit)


def filter_author(logs: Iterator[LogEntry], author: str) -> Iterator[LogEntry]:
    """
    Only keep commits from a specific author
    """

    return filter(lambda l: l.author == author, logs)


def fix_durations(logs: Iterator[LogEntry]) -> Iterator[LogEntry]:
    """
    Sorts the commits chronologically and looks, based on durations, if two
    commits are overlapping in time. If so, the duration is adjusted.
    """

    logs = sorted(logs, key=lambda l: l.end_date)

    if not len(logs):
        return []

    out = [logs[0]]

    for p, n in n_grams(logs, 2):
        duration = min(n.duration, (n.end_date - p.end_date).seconds)
        out.append(n.patch(duration=duration))

    return out


def zero_out(logs: Iterator[LogEntry]) -> Iterator[LogEntry]:
    """
    In case some commits were made simultaneously on different repos, some
    durations will be equal to zero or one. This removes those commits as they
    don't really matter.
    """

    return filter(lambda l: l.duration > 1, logs)


def clean_titles(logs: Iterator[LogEntry], exps: List[str]) \
        -> Iterator[LogEntry]:
    """
    Cleans the titles using the provided list of regular expressions. If none
    of the expressions match, then only the first line is kept.
    """

    for log in logs:
        title = log.title
        matched = False

        for exp in exps:
            if not isinstance(exp, str):
                continue

            m = re.search(exp, title, re.M)

            if m:
                title = m.group(1).strip()
                matched = True
                break

        if not matched:
            title = title.split('\n')[0].strip()

        yield log.patch(title=title)


def export(logs: Iterator[LogEntry], output_path: str) -> None:
    """
    Exports the list of logs into a CSV file for further processing.
    """

    with open(output_path, encoding='utf-8', mode='w') as f:
        w = csv.writer(f)
        w.writerow(LogEntry._fields)

        for log in logs:
            w.writerow(log)


def main():
    """
    Generates a timesheet based on a list of commits. As you can work on
    several repos at a time, this can look at all of them at once in order to
    make more precise guesses on durations.
    """

    args = parse_args()

    logs = chain(*[extract_logs(r, args.start_up_time) for r in args.repos])
    logs = filter_author(logs, args.author)
    logs = fix_durations(logs)
    logs = zero_out(logs)
    logs = clean_titles(logs, [args.title_exp])

    export(logs, args.output)


if __name__ == '__main__':
    main()
