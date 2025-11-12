#!/usr/bin/env python3
"""
Student Benchmark Suite for Model Evaluation

Comprehensive benchmarking tool for comparing model performance.
Useful for evaluating fine-tuned models against base models.

Usage:
    # Benchmark single model
    python student_benchmark.py --model llama3.1:8b

    # Compare multiple models
    python student_benchmark.py --models llama3.1:8b student-chatbot mistral:7b

    # Custom prompts
    python student_benchmark.py --model student-chatbot --prompts prompts.txt

    # Export results
    python student_benchmark.py --model student-chatbot --output results.json
"""

import os
import sys
import time
import json
import argparse
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import requests
    from tabulate import tabulate
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests tabulate")
    import requests
    from tabulate import tabulate


# Default benchmark prompts
DEFAULT_PROMPTS = [
    # General knowledge
    "Explain what photosynthesis is in 2-3 sentences.",

    # Technical explanation
    "What is a neural network and how does it work?",

    # Translation
    "Translate 'Good morning, how are you?' to German.",

    # Coding
    "Write a Python function to find the factorial of a number.",

    # Creative writing
    "Write a short paragraph about the importance of education.",

    # Math reasoning
    "If a train travels at 60 km/h for 2.5 hours, how far does it travel?",

    # Language understanding
    "What is the difference between 'affect' and 'effect'?",

    # Summarization
    "Summarize the water cycle in simple terms.",

    # Problem solving
    "How would you approach debugging a program that crashes randomly?",

    # Comparative analysis
    "Compare and contrast renewable and non-renewable energy sources."
]


class ModelBenchmark:
    """Benchmark runner for model evaluation"""

    def __init__(
        self,
        api_url: str = "http://localhost:11434",
        timeout: int = 60
    ):
        """
        Initialize benchmark runner

        Args:
            api_url: Ollama API URL
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.timeout = timeout
        self.session = requests.Session()

    def run_inference(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Run inference on a single prompt

        Args:
            model: Model name
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with results and metrics
        """
        try:
            start_time = time.time()

            response = self.session.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=self.timeout
            )

            elapsed_time = time.time() - start_time

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "latency_sec": elapsed_time
                }

            data = response.json()

            # Extract metrics
            eval_duration_ns = data.get("eval_duration", 0)
            eval_duration_sec = eval_duration_ns / 1_000_000_000

            total_tokens = data.get("eval_count", 0)
            tokens_per_sec = total_tokens / eval_duration_sec if eval_duration_sec > 0 else 0

            return {
                "success": True,
                "response": data.get("response", ""),
                "latency_sec": elapsed_time,
                "eval_duration_sec": eval_duration_sec,
                "total_tokens": total_tokens,
                "tokens_per_sec": tokens_per_sec,
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "load_duration_ms": data.get("load_duration", 0) / 1_000_000
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Request timeout after {self.timeout}s",
                "latency_sec": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_sec": time.time() - start_time
            }

    def benchmark_model(
        self,
        model: str,
        prompts: List[str],
        max_tokens: int = 200,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Benchmark a model with multiple prompts

        Args:
            model: Model name
            prompts: List of prompts
            max_tokens: Maximum tokens per generation
            verbose: Print progress

        Returns:
            Dictionary with benchmark results
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Benchmarking: {model}")
            print(f"Prompts: {len(prompts)}")
            print(f"{'='*60}\n")

        results = []
        successful = 0
        failed = 0

        for i, prompt in enumerate(prompts, 1):
            if verbose:
                print(f"[{i}/{len(prompts)}] Running prompt: {prompt[:50]}...")

            result = self.run_inference(model, prompt, max_tokens)
            result["prompt"] = prompt
            results.append(result)

            if result["success"]:
                successful += 1
                if verbose:
                    print(f"  ✓ {result['total_tokens']} tokens in {result['latency_sec']:.2f}s "
                          f"({result['tokens_per_sec']:.1f} tokens/sec)")
            else:
                failed += 1
                if verbose:
                    print(f"  ✗ Failed: {result['error']}")

        # Calculate statistics
        successful_results = [r for r in results if r["success"]]

        if successful_results:
            latencies = [r["latency_sec"] for r in successful_results]
            throughputs = [r["tokens_per_sec"] for r in successful_results]
            tokens = [r["total_tokens"] for r in successful_results]

            stats = {
                "avg_latency_sec": statistics.mean(latencies),
                "median_latency_sec": statistics.median(latencies),
                "min_latency_sec": min(latencies),
                "max_latency_sec": max(latencies),
                "std_latency_sec": statistics.stdev(latencies) if len(latencies) > 1 else 0,

                "avg_tokens_per_sec": statistics.mean(throughputs),
                "median_tokens_per_sec": statistics.median(throughputs),
                "min_tokens_per_sec": min(throughputs),
                "max_tokens_per_sec": max(throughputs),

                "avg_tokens": statistics.mean(tokens),
                "total_tokens": sum(tokens)
            }
        else:
            stats = {}

        return {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "prompts_count": len(prompts),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(prompts) if prompts else 0,
            "statistics": stats,
            "results": results
        }

    def compare_models(
        self,
        models: List[str],
        prompts: List[str],
        max_tokens: int = 200,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Compare multiple models

        Args:
            models: List of model names
            prompts: List of prompts
            max_tokens: Maximum tokens per generation
            verbose: Print progress

        Returns:
            Dictionary with comparison results
        """
        all_results = {}

        for model in models:
            result = self.benchmark_model(model, prompts, max_tokens, verbose)
            all_results[model] = result

        return {
            "timestamp": datetime.now().isoformat(),
            "models": models,
            "prompts_count": len(prompts),
            "results": all_results,
            "comparison": self._generate_comparison(all_results)
        }

    def _generate_comparison(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison summary"""
        comparison = []

        for model, data in results.items():
            stats = data.get("statistics", {})
            if stats:
                comparison.append({
                    "model": model,
                    "avg_latency": stats.get("avg_latency_sec", 0),
                    "avg_throughput": stats.get("avg_tokens_per_sec", 0),
                    "success_rate": data.get("success_rate", 0),
                    "total_tokens": stats.get("total_tokens", 0)
                })

        # Sort by throughput (descending)
        comparison.sort(key=lambda x: x["avg_throughput"], reverse=True)

        return comparison


def load_prompts_from_file(filepath: str) -> List[str]:
    """Load prompts from a text file (one per line)"""
    try:
        with open(filepath, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
        return prompts
    except Exception as e:
        print(f"Error loading prompts from {filepath}: {e}")
        return []


def print_comparison_table(comparison: List[Dict[str, Any]]):
    """Print comparison results as a table"""
    headers = ["Model", "Avg Latency (s)", "Throughput (tok/s)", "Success Rate", "Total Tokens"]
    rows = [
        [
            item["model"],
            f"{item['avg_latency']:.2f}",
            f"{item['avg_throughput']:.1f}",
            f"{item['success_rate']*100:.1f}%",
            item["total_tokens"]
        ]
        for item in comparison
    ]

    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def save_results(results: Dict[str, Any], output_path: str):
    """Save results to JSON file"""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {output_path}")
    except Exception as e:
        print(f"\n✗ Error saving results: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Benchmark models for performance evaluation"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Single model to benchmark"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Multiple models to compare"
    )
    parser.add_argument(
        "--prompts",
        type=str,
        help="Path to prompts file (one per line)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=200,
        help="Maximum tokens per generation (default: 200)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API URL (default: http://localhost:11434)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    # Determine models to benchmark
    if args.models:
        models = args.models
    elif args.model:
        models = [args.model]
    else:
        print("Error: Please specify --model or --models")
        parser.print_help()
        sys.exit(1)

    # Load prompts
    if args.prompts:
        prompts = load_prompts_from_file(args.prompts)
        if not prompts:
            print("Error: No prompts loaded from file")
            sys.exit(1)
    else:
        prompts = DEFAULT_PROMPTS
        if not args.quiet:
            print(f"Using {len(prompts)} default benchmark prompts")

    # Initialize benchmark
    benchmark = ModelBenchmark(api_url=args.api_url)

    # Run benchmark
    verbose = not args.quiet

    if len(models) == 1:
        # Single model benchmark
        results = benchmark.benchmark_model(
            models[0],
            prompts,
            args.max_tokens,
            verbose
        )

        if verbose:
            stats = results.get("statistics", {})
            if stats:
                print(f"\n{'='*60}")
                print(f"SUMMARY: {models[0]}")
                print(f"{'='*60}")
                print(f"Success Rate: {results['success_rate']*100:.1f}%")
                print(f"Avg Latency: {stats['avg_latency_sec']:.2f}s")
                print(f"Avg Throughput: {stats['avg_tokens_per_sec']:.1f} tokens/sec")
                print(f"Total Tokens: {stats['total_tokens']}")
                print(f"{'='*60}\n")

    else:
        # Multi-model comparison
        results = benchmark.compare_models(
            models,
            prompts,
            args.max_tokens,
            verbose
        )

        if verbose:
            print_comparison_table(results["comparison"])

    # Save results
    if args.output:
        save_results(results, args.output)

    # Exit with appropriate code
    if isinstance(results, dict):
        if "results" in results:  # Comparison
            success = all(
                r.get("success_rate", 0) > 0
                for r in results["results"].values()
            )
        else:  # Single model
            success = results.get("success_rate", 0) > 0
    else:
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
