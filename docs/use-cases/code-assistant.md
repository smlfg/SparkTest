# Use Case: Code Assistant Fine-tuning

**Complete guide to fine-tuning models for code generation and assistance**

---

## Overview

This guide covers fine-tuning models for code-related tasks including code generation, code completion, bug fixing, code explanation, and documentation generation.

**What you'll learn**:
- Preparing code datasets
- Best models for code tasks
- Training configurations
- Evaluation strategies
- Safety and security considerations

**Time required**: 4-8 hours (training) + 1 hour (setup)

---

## Use Cases

### 1. Code Generation
- Generate functions from natural language descriptions
- Create complete programs from specifications
- Implement algorithms from descriptions
- Convert pseudocode to real code

### 2. Code Completion
- Auto-complete function bodies
- Suggest next lines of code
- Complete partial implementations
- Fill in boilerplate code

### 3. Code Translation
- Convert between programming languages (Python → JavaScript)
- Modernize legacy code
- Transpile code (TypeScript → JavaScript)

### 4. Bug Fixing
- Identify and fix bugs in code
- Suggest error corrections
- Debug error messages
- Optimize inefficient code

### 5. Code Explanation
- Generate docstrings and comments
- Explain complex code in plain language
- Create documentation from code
- Answer questions about code behavior

### 6. Test Generation
- Generate unit tests from code
- Create test cases from specifications
- Generate edge case tests

---

## Dataset Format

### Code Generation Format

**JSONL format** (recommended):
```json
{"instruction": "Write a function to reverse a string", "code": "def reverse_string(s):\n    return s[::-1]"}
{"instruction": "Create a binary search implementation", "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"}
```

**With context**:
```json
{"instruction": "Add error handling to this function", "input": "def divide(a, b):\n    return a / b", "output": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b"}
```

### Code Completion Format

```json
{"prefix": "def fibonacci(n):\n    \"\"\"Calculate the nth Fibonacci number\"\"\"\n    if n <= 1:\n        return n\n    ", "suffix": "", "middle": "return fibonacci(n-1) + fibonacci(n-2)"}
```

### Code Question-Answering

```json
{"question": "What does this function do?", "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)", "answer": "This function calculates the factorial of a number n using recursion. The factorial of n (n!) is the product of all positive integers less than or equal to n."}
```

### Multi-Language Dataset

```json
{"source_lang": "python", "target_lang": "javascript", "source_code": "def greet(name):\n    return f'Hello, {name}!'", "target_code": "function greet(name) {\n    return `Hello, ${name}!`;\n}"}
```

---

## Data Collection

### Sources

**1. GitHub Repositories**:
```python
from github import Github

g = Github("your_token")

# Search for high-quality Python repos
repos = g.search_repositories("language:python stars:>1000")

for repo in repos[:100]:
    # Clone and extract functions
    # Filter for good documentation
    # Create instruction-code pairs
```

**2. Coding Challenge Platforms**:
- LeetCode solutions
- HackerRank problems
- Codeforces submissions
- Project Euler solutions

**Format example**:
```json
{"instruction": "Find the longest palindrome substring", "code": "def longest_palindrome(s):\n    # Implementation", "test_cases": "assert longest_palindrome('babad') == 'bab'\nassert longest_palindrome('cbbd') == 'bb'"}
```

**3. Stack Overflow**:
```python
# Extract Q&A pairs where answer includes code
import requests

# Search for Python questions
api_url = "https://api.stackexchange.com/2.3/questions"
params = {
    "tagged": "python",
    "filter": "withbody",
    "accepted": True
}

# Extract question → code pairs
# Filter for quality (score > 10, accepted answer)
```

**4. Documentation Examples**:
- Official library docs
- Tutorial code examples
- API usage examples

**5. Synthetic Data**:
```python
# Use GPT-4 to generate training examples
prompts = [
    "Generate a Python function that sorts a list using quicksort",
    "Create a JavaScript class for a binary tree",
    "Write a SQL query to find duplicate records",
]

# Review and validate generated code
# Ensure code runs correctly
```

### Data Quality Requirements

✅ **Syntactically correct**: All code must parse and run
✅ **Well-documented**: Include docstrings/comments
✅ **Following conventions**: PEP 8 (Python), Standard (JavaScript)
✅ **Tested**: Include test cases when possible
✅ **Diverse**: Various problem types and difficulties
✅ **Clean**: Remove credentials, internal info
✅ **Licensed**: Only use permissively licensed code
✅ **Secure**: No vulnerabilities or malicious code

### Code Validation

**Automated checks**:
```python
import ast
import subprocess

def validate_python_code(code):
    """Ensure code is syntactically correct and runnable"""
    try:
        # Check syntax
        ast.parse(code)

        # Try to run (with timeout)
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            timeout=5
        )

        # Check for common issues
        if "import os" in code or "subprocess" in code:
            print("Warning: Potentially dangerous code")
            return False

        return True
    except SyntaxError:
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# Filter dataset
valid_examples = [ex for ex in dataset if validate_python_code(ex['code'])]
```

### Minimum Data Requirements

| Task | Minimum Examples | Recommended |
|------|------------------|-------------|
| Simple completion | 1,000 | 10,000 |
| Function generation | 5,000 | 20,000 |
| Multi-language translation | 10,000 | 50,000 |
| Bug fixing | 2,000 | 10,000 |
| Complex programs | 5,000 | 30,000 |

---

## Recommended Configuration

### Model Selection

**For simple completion/generation**:
```yaml
model_name: "Salesforce/codegen-350M-mono"
# Language: Python
# Memory: ~2GB
# Training time: 2-3 hours
```

**For general code assistance** (recommended):
```yaml
model_name: "Salesforce/codegen-2B-multi"
# Languages: Python, Java, JavaScript
# Memory: ~8GB
# Training time: 6-8 hours
```

**For advanced code generation**:
```yaml
model_name: "codellama/CodeLlama-7b-hf"
# Best for code reasoning
# Memory: ~28GB (with optimizations)
# Training time: 12-16 hours
```

**For production (highest quality)**:
```yaml
model_name: "codellama/CodeLlama-13b-Instruct-hf"
# Best instruction-following
# Memory: ~52GB (requires FSDP)
# Training time: 20-24 hours
```

**For specific languages**:
```yaml
# Python-only
model_name: "Salesforce/codegen-2B-mono"

# Multi-language (100+ languages)
model_name: "bigcode/starcoderbase-7b"
```

### Training Configuration

**Recommended settings for code generation**:

```yaml
# Model
model_name: "Salesforce/codegen-2B-multi"
use_lora: true
lora_config:
  r: 32
  alpha: 32
  dropout: 0.05
  target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

# Training
num_epochs: 3
learning_rate: 5e-5
lr_scheduler: "cosine"
warmup_steps: 500

# Batch size (adjust for GPU)
per_device_train_batch_size: 4
gradient_accumulation_steps: 8  # Effective batch: 32

# Optimization
mixed_precision: "bf16"
gradient_checkpointing: true
max_grad_norm: 1.0

# Code-specific settings
max_length: 2048  # Longer for complete functions
padding: "max_length"
truncation: true

# Saving
save_strategy: "steps"
save_steps: 1000
save_total_limit: 3

# Evaluation
evaluation_strategy: "steps"
eval_steps: 500
load_best_model_at_end: true
metric_for_best_model: "eval_loss"

# Early stopping
early_stopping_patience: 3
```

**For code completion** (FIM - Fill-in-the-Middle):
```yaml
# Enable Fill-in-the-Middle training
fim_rate: 0.5  # 50% of examples use FIM format
fim_spm_rate: 0.5  # Suffix-prefix-middle ordering

# Example FIM format:
# Input: <fim_prefix>def add(<fim_suffix>):<fim_middle>
# Output: a, b
```

---

## Training Process

### Step 1: Prepare Code Dataset

**Extract functions from files**:
```python
import ast
import os

def extract_functions(file_path):
    """Extract all functions from a Python file"""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Get function source
            code = ast.get_source_segment(f.read(), node)

            # Get docstring as instruction
            docstring = ast.get_docstring(node) or f"Implement {node.name}"

            functions.append({
                "instruction": docstring,
                "code": code
            })

    return functions

# Process repository
dataset = []
for root, dirs, files in os.walk("repository/"):
    for file in files:
        if file.endswith(".py"):
            dataset.extend(extract_functions(os.path.join(root, file)))

# Save
import json
with open("code_dataset.jsonl", "w") as f:
    for item in dataset:
        f.write(json.dumps(item) + "\n")
```

**Create train/val/test split**:
```python
from sklearn.model_selection import train_test_split

# Load
with open("code_dataset.jsonl") as f:
    data = [json.loads(line) for line in f]

# Split
train, temp = train_test_split(data, test_size=0.2, random_state=42)
val, test = train_test_split(temp, test_size=0.5, random_state=42)

# Save splits
for split, split_data in [("train", train), ("val", val), ("test", test)]:
    with open(f"{split}.jsonl", "w") as f:
        for item in split_data:
            f.write(json.dumps(item) + "\n")
```

### Step 2: Upload Dataset

1. **Datasets** → **Upload New**
2. Upload `train.jsonl`, `val.jsonl`, `test.jsonl`
3. Metadata:
   - Name: `python-code-generation-v1`
   - Type: `Code Generation`
   - Language: `Python`
4. Wait for validation

### Step 3: Configure Training

1. **Training** → **New Job**
2. Template: **Code Generation**
3. Select dataset
4. Base model: `Salesforce/codegen-2B-multi`
5. Configure parameters
6. Name: `python-code-assistant-v1`

### Step 4: Monitor Training

**Key metrics**:
- **Training Loss**: Should decrease (target: <0.5)
- **Validation Loss**: Track for overfitting
- **Code Perplexity**: Lower is better
- **Exact Match**: Percentage of perfect generations (if applicable)

**Expected timeline** (CodeGen-2B, 10K examples):
- 350M model: 2-3 hours
- 2B model: 6-8 hours
- 7B model: 12-16 hours

---

## Evaluation Metrics

### Pass@K

**Most important metric for code**: Percentage of problems solved correctly in K attempts

```python
def evaluate_pass_at_k(model, problems, k=1):
    """
    Evaluate how many problems are solved in K attempts
    """
    solved = 0

    for problem in problems:
        # Generate K solutions
        solutions = [model.generate(problem['instruction']) for _ in range(k)]

        # Test each solution
        for solution in solutions:
            if test_code(solution, problem['test_cases']):
                solved += 1
                break  # Problem solved, move to next

    return solved / len(problems)

# Example
pass_at_1 = evaluate_pass_at_k(model, test_problems, k=1)  # 30%
pass_at_10 = evaluate_pass_at_k(model, test_problems, k=10)  # 60%

print(f"Pass@1: {pass_at_1:.2%}")  # 30%
print(f"Pass@10: {pass_at_10:.2%}")  # 60%
```

**Targets**:
- Pass@1: >30% (good), >50% (excellent)
- Pass@10: >60% (good), >80% (excellent)

### Exact Match

**Percentage of perfect code generations**:
```python
exact_matches = sum(1 for pred, ref in zip(predictions, references) if pred.strip() == ref.strip())
exact_match_rate = exact_matches / len(predictions)

# Target: >20% for complex tasks
```

### Code BLEU

**Measure similarity considering code structure**:
```python
from codebleu import calc_codebleu

result = calc_codebleu(
    references=[["def add(a, b):\n    return a + b"]],
    predictions=["def add(a, b):\n    result = a + b\n    return result"],
    lang="python"
)

print(f"CodeBLEU: {result['codebleu']:.3f}")  # 0.85

# Target: >0.60 (good), >0.75 (excellent)
```

### Functional Correctness

**Does the code actually work?**:
```python
import subprocess
import tempfile

def test_functional_correctness(code, test_cases):
    """
    Run code against test cases
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.write("\n\n")
        f.write(test_cases)
        temp_file = f.name

    try:
        # Run tests
        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    finally:
        os.unlink(temp_file)

# Test on dataset
correct = sum(1 for ex in test_set if test_functional_correctness(ex['generated_code'], ex['test_cases']))
accuracy = correct / len(test_set)

# Target: >70%
```

### Compilation Rate

**Percentage of syntactically valid code**:
```python
import ast

def check_syntax(code, language="python"):
    """Check if code has valid syntax"""
    try:
        if language == "python":
            ast.parse(code)
        # Add other language parsers
        return True
    except SyntaxError:
        return False

# Must be >95%
```

---

## Advanced Techniques

### Instruction Tuning

**Format with clear instructions**:
```json
{"instruction": "Write a Python function that takes a list of integers and returns the sum of all even numbers. Include error handling for non-integer inputs.", "code": "def sum_even_numbers(numbers):\n    \"\"\"\n    Sum all even numbers in a list.\n    \n    Args:\n        numbers (list): List of integers\n        \n    Returns:\n        int: Sum of even numbers\n        \n    Raises:\n        TypeError: If list contains non-integers\n    \"\"\"\n    if not all(isinstance(n, int) for n in numbers):\n        raise TypeError('All elements must be integers')\n    \n    return sum(n for n in numbers if n % 2 == 0)"}
```

### Few-Shot Examples

**Include examples in prompt**:
```python
prompt = """Here are some examples:

Example 1:
Instruction: Write a function to check if a number is prime
Code:
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

Example 2:
Instruction: Write a function to find the maximum element in a list
Code:
def find_max(lst):
    if not lst:
        raise ValueError("List is empty")
    return max(lst)

Now generate:
Instruction: Write a function to calculate the factorial of a number
Code:
"""
```

### Chain-of-Thought for Code

**Include reasoning steps**:
```json
{"instruction": "Write a function to find the longest common substring", "reasoning": "1. Use dynamic programming\n2. Create 2D matrix to store lengths\n3. Track maximum length and position\n4. Extract substring from original string", "code": "def longest_common_substring(s1, s2):\n    # Implementation with DP..."}
```

### Test-Driven Generation

**Generate tests first, then code**:
```python
# Step 1: Generate tests
test_prompt = "Write pytest tests for a function that reverses a string"
tests = model.generate(test_prompt)

# Step 2: Generate implementation
impl_prompt = f"Write a function that passes these tests:\n{tests}"
implementation = model.generate(impl_prompt)
```

---

## Safety & Security

### Code Review Checklist

✅ **No hardcoded credentials**: Check for API keys, passwords
✅ **No malicious code**: No `os.system()`, `eval()`, `exec()` with user input
✅ **Input validation**: Proper error handling
✅ **No SQL injection**: Use parameterized queries
✅ **No path traversal**: Validate file paths
✅ **No infinite loops**: Reasonable bounds on iterations
✅ **Resource limits**: Memory and time constraints

### Automated Security Scanning

```python
import re

def security_scan(code):
    """Basic security checks for generated code"""
    issues = []

    # Check for dangerous functions
    dangerous = ['eval', 'exec', 'compile', '__import__']
    for func in dangerous:
        if re.search(rf'\b{func}\s*\(', code):
            issues.append(f"Dangerous function: {func}")

    # Check for hardcoded secrets
    if re.search(r'(password|api_key|secret)\s*=\s*["\']', code, re.I):
        issues.append("Possible hardcoded secret")

    # Check for SQL injection vulnerability
    if re.search(r'execute\s*\(\s*["\'].*%s', code):
        issues.append("Possible SQL injection vulnerability")

    return issues

# Filter unsafe code
safe_examples = [ex for ex in dataset if not security_scan(ex['code'])]
```

---

## Deployment Checklist

✅ **Pass@1 >30%**: Functional correctness
✅ **Compilation rate >95%**: Syntactically valid
✅ **Security scan**: No dangerous patterns
✅ **Edge cases tested**: Empty inputs, large inputs, errors
✅ **Response time <3s**: Fast enough for interactive use
✅ **Documentation**: Clear limitations stated
✅ **Human review**: Sample outputs reviewed by developers
✅ **Logging**: Track generations for monitoring

---

## Common Pitfalls

### Problem 1: Generated Code Doesn't Run

**Symptom**: Syntax errors, runtime errors

**Solutions**:
```yaml
# Increase training data quality
# Filter for only runnable code

# Post-processing
use_syntax_checker: true
retry_on_syntax_error: true
max_retries: 3
```

### Problem 2: Code Works But Inefficient

**Symptom**: Generates O(n²) when O(n) possible

**Solutions**:
- Include efficiency requirements in instructions
- Add performance tests to dataset
- Train on optimized code examples

### Problem 3: Generates Outdated Code

**Symptom**: Uses deprecated APIs

**Solutions**:
- Filter training data by date
- Use recent repositories
- Include version specifications in instructions

---

## Example Datasets

**Download**:
- [Python Function Generation](../examples/datasets/python-functions.jsonl)
- [JavaScript Code Completion](../examples/datasets/js-completion.jsonl)
- [Multi-Language Translation](../examples/datasets/code-translation.jsonl)
- [Bug Fixing Examples](../examples/datasets/bug-fixes.jsonl)

**External**:
- CodeXGLUE: Multiple code tasks
- The Stack: 3TB of permissively licensed code
- CodeSearchNet: 6M functions with documentation

---

## Resources

**Models**:
- [CodeGen](https://github.com/salesforce/CodeGen)
- [Code Llama](https://github.com/facebookresearch/codellama)
- [StarCoder](https://github.com/bigcode-project/starcoder)

**Evaluation**:
- [HumanEval](https://github.com/openai/human-eval): Python benchmark
- [MBPP](https://github.com/google-research/google-research/tree/master/mbpp): Python problems
- [CodeXGLUE](https://github.com/microsoft/CodeXGLUE): Multi-task benchmark

**Tools**:
- [CodeBLEU](https://github.com/microsoft/CodeXGLUE/tree/main/code-to-code-trans/CodeBLEU)
- [tree-sitter](https://tree-sitter.github.io/): Code parsing
- [Bandit](https://github.com/PyCQA/bandit): Python security scanner

**Support**:
- Forum: forum.platform-url.com/c/code-generation
- Slack: #code-assistant
- Email: support@platform-url.com

---

*Last updated: January 12, 2025*
