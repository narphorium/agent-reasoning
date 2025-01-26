#!/usr/bin/env python3
import argparse
from pathlib import Path
import subprocess
from typing import Set

from datasets import load_dataset
from tqdm import tqdm


def get_repos_for_split(split: str) -> Set[str]:
    """Get unique repository names from a dataset split."""
    dataset = load_dataset("princeton-nlp/SWE-bench")
    return {instance['repo'] for instance in dataset[split]}


def clone_repo(repo: str, repos_path: Path) -> None:
    """Clone a GitHub repository to the specified path."""
    repo_name = repo.split('/')[-1]
    repo_path = repos_path / repo_name
    
    if repo_path.exists():
        print(f"Repository {repo_name} already exists, skipping...")
        return
        
    github_url = f"https://github.com/{repo}"
    try:
        subprocess.run(
            ["git", "clone", github_url, str(repo_path)],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error cloning {repo}: {e.stderr}")


def main():
    parser = argparse.ArgumentParser(description='Clone repositories from SWE-Bench dataset')
    parser.add_argument('repos_path', type=str, help='Path where repositories should be cloned')
    parser.add_argument(
        '--split', 
        type=str,
        default="test",
        choices=["train", "test", "validation", "dev"],
        help='Dataset split to use'
    )
    args = parser.parse_args()

    # Create repos directory if it doesn't exist
    repos_path = Path(args.repos_path).expanduser()
    repos_path.mkdir(parents=True, exist_ok=True)

    # Get unique repos for the split
    repos = get_repos_for_split(args.split)
    print(f"Found {len(repos)} repositories to clone")

    # Clone each repo
    for repo in tqdm(repos, desc=f"Cloning repositories for {args.split} split"):
        clone_repo(repo, repos_path)


if __name__ == "__main__":
    main() 