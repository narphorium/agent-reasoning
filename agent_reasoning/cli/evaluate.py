#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional
from statistics import mean

from datasets import load_dataset
from dotenv import load_dotenv
from tqdm import tqdm

from agent_reasoning import get_py_tree, get_patch_files, match_files
from agent_reasoning.models import ModelClient


def create_file_selection_prompt(tree_string: str, problem_statement: str) -> str:
    return f"""
You are an expert software architect.
Your task is to analyze a repository of code and determine which files need to be changed for the given task.
Format your response as a list of file names, one per line.

The repository directory structure is:
{tree_string}

The task is:
{problem_statement}
"""


def get_cached_tree(repo_path: Path) -> Optional[str]:
    """Get cached tree from map.md if it exists."""
    map_file = Path("results") / repo_path.name / "map.md"
    if map_file.exists():
        with open(map_file) as f:
            content = f.read()
            return content.strip()
    return None


def cache_tree(repo_path: Path, tree_string: str) -> None:
    """Cache the generated tree to map.md."""
    results_dir = Path("results") / repo_path.name
    results_dir.mkdir(parents=True, exist_ok=True)
    
    map_file = results_dir / "map.md"
    with open(map_file, "w") as f:
        f.write(tree_string)


def evaluate_instance(
    instance: Dict,
    model_client: ModelClient,
    repos_path: Path,
    output_path: Path
) -> Optional[Dict]:
    result_file = output_path / f"{instance['instance_id']}.json"
    if result_file.exists():
        # Load and return existing results instead of returning None
        with open(result_file, 'r') as f:
            return json.load(f)

    repo_path = repos_path / instance['repo'].split('/')[-1]
    
    trajectory = []
    
    # Try to get cached tree, generate if not exists
    tree_string = get_cached_tree(repo_path)
    if tree_string is None:
        tree_string = get_py_tree(str(repo_path))
        cache_tree(repo_path, tree_string)
    
    # Create and log initial prompt
    prompt = create_file_selection_prompt(tree_string, instance['problem_statement'])
    trajectory.append({
        "role": "user",
        "content": prompt
    })

    # Get model response
    response = model_client.generate([{"role": "user", "content": prompt}])
    trajectory.append({"role": "assistant", "content": response})

    # Extract files from patches
    code_files = get_patch_files(instance['patch'])
    test_files = get_patch_files(instance['test_patch'])
    response_files = response.splitlines()

    # Calculate metrics
    code_results = match_files(response_files, code_files)
    test_results = match_files(response_files, test_files)

    # Remove overlapping files from results
    code_results = code_results.exclude_matches(test_results)
    test_results = test_results.exclude_matches(code_results)

    results = {
        "instance_id": instance["instance_id"],
        "code_precision": code_results.precision(),
        "code_recall": code_results.recall(),
        "test_precision": test_results.precision(),
        "test_recall": test_results.recall(),
        "code_results": code_results.to_json(),
        "test_results": test_results.to_json(),
        "trajectory": trajectory
    }

    # Save results
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)

    return results


def calculate_aggregate_metrics(results: List[Dict]) -> Dict[str, float]:
    """Calculate average metrics across all results."""
    metrics = {
        "code_precision": [],
        "code_recall": [],
        "test_precision": [],
        "test_recall": []
    }
    
    for result in results:
        if result is None:
            continue
        for metric in metrics:
            metrics[metric].append(result[metric])
    
    return {
        metric: mean(values) if values else 0.0 
        for metric, values in metrics.items()
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate model performance on file selection task')
    parser.add_argument('model', help='Name of the model to evaluate')
    parser.add_argument('prompt', help='Name of the prompt to use')
    parser.add_argument('repos_path', help='Path to the root directory containing all repositories')
    parser.add_argument('--split', help='Dataset split to evaluate on', 
                       default="test", choices=["train", "test", "validation"])
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Create results directory
    timestamp = datetime.now().strftime("%Y-%m-%d")
    results_dir = Path("results") / f"{timestamp}-{args.prompt}-{args.model}"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Initialize model client
    model_client = ModelClient(args.model)

    # Load dataset
    dataset = load_dataset("princeton-nlp/SWE-bench")
    
    # Process each instance
    all_results = []
    for instance in tqdm(dataset[args.split], desc=f"Evaluating {args.split} instances"):
        try:
            results = evaluate_instance(
                instance=instance,
                model_client=model_client,
                repos_path=Path(args.repos_path).expanduser(),
                output_path=results_dir
            )
            all_results.append(results)
        except Exception as e:
            print(f"\nError processing {instance['instance_id']}: {str(e)}")
            continue

    # Calculate and display aggregate metrics
    aggregate_metrics = calculate_aggregate_metrics(all_results)
    print("\nFinal Results:")
    print(f"Code Precision: {aggregate_metrics['code_precision']:.2f}")
    print(f"Code Recall: {aggregate_metrics['code_recall']:.2f}")
    print(f"Test Precision: {aggregate_metrics['test_precision']:.2f}")
    print(f"Test Recall: {aggregate_metrics['test_recall']:.2f}")

    # Save aggregate metrics
    with open(results_dir / "aggregate_metrics.json", 'w') as f:
        json.dump(aggregate_metrics, f, indent=2)


if __name__ == "__main__":
    main() 