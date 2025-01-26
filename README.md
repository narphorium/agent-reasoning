# Agent Reasoning

Tools for evaluating and analyzing AI agent reasoning capabilities.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/narphorium/agent-reasoning.git
cd agent-reasoning
```

2. Install uv if you haven't already:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Create a virtual environment and install the package:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix
# OR
.venv\Scripts\activate     # On Windows

# Install in editable mode
uv pip install -e .
```

4. Set up environment variables:

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Then edit `.env` with your API keys. The following keys are supported:

```bash
# OpenAI API key for GPT models
OPENAI_API_KEY=sk-...

# Anthropic API key for Claude models
ANTHROPIC_API_KEY=sk-ant-...

# Google API key for Gemini models
GOOGLE_API_KEY=...
```

5. Set up Ollama (for local models):

First install Ollama following the [official instructions](https://ollama.ai/download).

Then pull and run the DeepSeek model:

```bash
# Pull the model
ollama pull hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q8_0
```

## Usage

### Clone SWE-Bench Repositories

Before running evaluations, you'll need to clone the repositories from the SWE-Bench dataset. Use the clone-repos script:

```bash
clone-repos <repos_path> --split test
```

Or using Python directly:

```bash
python scripts/clone_repos.py <repos_path> --split test
```

Arguments:

- `repos_path`: Directory where repositories should be cloned
- `--split`: Dataset split to use (choices: "train", "test", "validation", "dev", default: "test")

Example:

```bash
clone-repos ~/Documents/SWE-Bench --split test
```

The script will:

- Create the target directory if it doesn't exist
- Get unique repositories from the specified dataset split
- Clone each repository (skipping any that already exist)
- Show progress with a progress bar

### Evaluation Script

The evaluation script measures how well different models can identify which files need to be modified for a given code change task.

You can run the evaluation script in two ways:

1. Using the installed command:

```bash
evaluate <model> <prompt> <repos_path> --split test
```

2. Using Python directly:

```bash
python scripts/evaluate.py <model> <prompt> <repos_path> --split test
```

Arguments:

- `model`: Name of the model to evaluate (e.g., "gpt-4", "claude-3", "o1-preview", "deepseek-8b")
- `prompt`: Name of the prompt strategy to use (e.g., "file-selection")
- `repos_path`: Path to the root directory containing all SWE-bench repositories
- `--split`: Dataset split to evaluate on (choices: "train", "test", "validation", default: "test")

Example:

```bash
evaluate o1-preview-2024-09-12 file-selection ~/Documents/SWE-Bench --split test
```

### Results

The script creates a timestamped results directory under `results/` with the format:

```
results/
  YYYY-MM-DD-HH-MM-SS-prompt-model/
    instance1.json
    instance2.json
    ...
    aggregate_metrics.json
```

Each instance result file contains:

- Instance evaluation metrics (precision and recall for code and test files)
- Detailed results showing true/false positives and negatives
- Complete conversation trajectory with the model

The aggregate_metrics.json file contains the averaged results across all evaluated instances.
