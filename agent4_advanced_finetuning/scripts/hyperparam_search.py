"""
Hyperparameter Search Script for Agent 4
Supports grid search, random search, and Bayesian optimization
"""

import argparse
import json
import os
import subprocess
import sys
import copy
from pathlib import Path
from typing import Dict, Any, List
import yaml
import random
import numpy as np


class HyperparameterSearcher:
    """Hyperparameter search orchestrator"""

    def __init__(self, search_config_path: str):
        with open(search_config_path) as f:
            self.config = yaml.safe_load(f)

        self.base_config_path = self.config["base_config"]
        with open(self.base_config_path) as f:
            self.base_config = yaml.safe_load(f)

        self.search_space = self.config["search_space"]
        self.search_method = self.config["search"]["method"]
        self.num_trials = self.config["search"]["num_trials"]
        self.metric = self.config["search"]["metric"]
        self.direction = self.config["search"]["direction"]

        self.results_dir = Path(self.config["output"]["results_dir"])
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.trials = []
        self.best_trial = None

        print(f"🔍 Hyperparameter Search initialized")
        print(f"   Method: {self.search_method}")
        print(f"   Trials: {self.num_trials}")
        print(f"   Metric: {self.metric} ({self.direction})")

    def generate_trial_configs(self) -> List[Dict[str, Any]]:
        """Generate trial configurations based on search method"""

        if self.search_method == "grid":
            return self._generate_grid_configs()
        elif self.search_method == "random":
            return self._generate_random_configs()
        elif self.search_method == "bayesian":
            return self._generate_bayesian_configs()
        else:
            raise ValueError(f"Unknown search method: {self.search_method}")

    def _generate_grid_configs(self) -> List[Dict[str, Any]]:
        """Generate all combinations for grid search"""
        import itertools

        # Extract values for each parameter
        param_values = {}
        for param_name, param_config in self.search_space.items():
            if param_config["type"] == "categorical":
                param_values[param_name] = param_config["values"]
            else:
                # For continuous parameters, sample a few values
                param_values[param_name] = self._sample_values(param_config, num_samples=3)

        # Generate all combinations
        keys = list(param_values.keys())
        combinations = list(itertools.product(*[param_values[k] for k in keys]))

        # Limit to num_trials
        if len(combinations) > self.num_trials:
            combinations = random.sample(combinations, self.num_trials)

        # Create configs
        configs = []
        for combination in combinations:
            config = copy.deepcopy(self.base_config)
            for key, value in zip(keys, combination):
                self._set_nested_value(config, key, value)
            configs.append(config)

        return configs

    def _generate_random_configs(self) -> List[Dict[str, Any]]:
        """Generate random configurations"""
        configs = []

        for _ in range(self.num_trials):
            config = copy.deepcopy(self.base_config)

            for param_name, param_config in self.search_space.items():
                value = self._sample_value(param_config)
                self._set_nested_value(config, param_name, value)

            configs.append(config)

        return configs

    def _generate_bayesian_configs(self) -> List[Dict[str, Any]]:
        """Generate configurations using Bayesian optimization"""
        print("⚠️  Bayesian optimization not fully implemented, falling back to random search")
        return self._generate_random_configs()

    def _sample_value(self, param_config: Dict[str, Any]):
        """Sample a single value from parameter configuration"""
        param_type = param_config["type"]

        if param_type == "categorical":
            return random.choice(param_config["values"])

        elif param_type == "uniform":
            return random.uniform(param_config["low"], param_config["high"])

        elif param_type == "loguniform":
            log_low = np.log(param_config["low"])
            log_high = np.log(param_config["high"])
            return np.exp(random.uniform(log_low, log_high))

        elif param_type == "int_uniform":
            return random.randint(param_config["low"], param_config["high"])

        else:
            raise ValueError(f"Unknown parameter type: {param_type}")

    def _sample_values(self, param_config: Dict[str, Any], num_samples: int = 3):
        """Sample multiple values from parameter configuration"""
        return [self._sample_value(param_config) for _ in range(num_samples)]

    def _set_nested_value(self, config: Dict, key_path: str, value: Any):
        """Set value in nested dictionary using dot notation (e.g., 'lora.r')"""
        keys = key_path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def run_trial(self, trial_id: int, trial_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single trial"""
        print(f"\n{'='*70}")
        print(f"Trial {trial_id + 1}/{self.num_trials}")
        print(f"{'='*70}")

        # Save trial config
        trial_dir = self.results_dir / f"trial_{trial_id:03d}"
        trial_dir.mkdir(exist_ok=True)

        config_path = trial_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(trial_config, f)

        # Override output directories
        trial_config["checkpointing"]["output_dir"] = str(trial_dir / "checkpoints")
        trial_config["experiment"]["name"] = f"trial_{trial_id:03d}"
        trial_config["experiment"]["output_dir"] = str(trial_dir)

        # Save updated config
        with open(config_path, "w") as f:
            yaml.dump(trial_config, f)

        # Run training
        try:
            cmd = [
                "python",
                "agent4_advanced_finetuning/scripts/train_pytorch.py",
                "--config", str(config_path)
            ]

            print(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["search"].get("timeout_per_trial", 3600)
            )

            if result.returncode != 0:
                print(f"❌ Trial failed with return code {result.returncode}")
                print(f"stderr: {result.stderr}")
                return None

            # Load experiment results
            experiment_file = trial_dir / f"trial_{trial_id:03d}.json"
            if not experiment_file.exists():
                print(f"⚠️  Experiment file not found: {experiment_file}")
                return None

            with open(experiment_file) as f:
                experiment_data = json.load(f)

            # Extract final metric
            if not experiment_data["metrics"]:
                print("⚠️  No metrics found in experiment")
                return None

            final_metrics = experiment_data["metrics"][-1]
            metric_value = final_metrics.get(self.metric)

            if metric_value is None:
                print(f"⚠️  Metric '{self.metric}' not found in final metrics")
                return None

            trial_result = {
                "trial_id": trial_id,
                "config": trial_config,
                "metric_value": metric_value,
                "all_metrics": final_metrics,
                "status": "completed"
            }

            print(f"✅ Trial completed: {self.metric} = {metric_value:.4f}")

            return trial_result

        except subprocess.TimeoutExpired:
            print(f"⏱️  Trial timed out after {self.config['search']['timeout_per_trial']}s")
            return {"trial_id": trial_id, "status": "timeout"}

        except Exception as e:
            print(f"❌ Trial failed with error: {e}")
            return {"trial_id": trial_id, "status": "failed", "error": str(e)}

    def run_search(self):
        """Execute hyperparameter search"""
        print(f"\n🚀 Starting hyperparameter search...")

        # Generate trial configurations
        trial_configs = self.generate_trial_configs()
        print(f"Generated {len(trial_configs)} trial configurations")

        # Run trials
        for trial_id, trial_config in enumerate(trial_configs):
            result = self.run_trial(trial_id, trial_config)

            if result and result.get("status") == "completed":
                self.trials.append(result)

                # Update best trial
                if self.best_trial is None:
                    self.best_trial = result
                else:
                    current_best = self.best_trial["metric_value"]
                    new_value = result["metric_value"]

                    if self.direction == "minimize":
                        if new_value < current_best:
                            self.best_trial = result
                            print(f"🏆 New best trial! {self.metric} = {new_value:.4f}")
                    else:
                        if new_value > current_best:
                            self.best_trial = result
                            print(f"🏆 New best trial! {self.metric} = {new_value:.4f}")

        # Save results
        self.save_results()

    def save_results(self):
        """Save search results"""
        results = {
            "search_config": self.config,
            "trials": self.trials,
            "best_trial": self.best_trial,
            "num_completed": len(self.trials),
            "num_total": self.num_trials
        }

        results_file = self.results_dir / "search_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📊 Results saved to: {results_file}")

        # Save best config
        if self.best_trial:
            best_config_path = self.config["output"]["best_config_path"]
            with open(best_config_path, "w") as f:
                yaml.dump(self.best_trial["config"], f)
            print(f"🏆 Best config saved to: {best_config_path}")

    def print_summary(self):
        """Print search summary"""
        print(f"\n{'='*70}")
        print("Hyperparameter Search Summary")
        print(f"{'='*70}")

        if not self.trials:
            print("No successful trials completed")
            return

        print(f"Completed trials: {len(self.trials)}/{self.num_trials}")

        if self.best_trial:
            print(f"\n🏆 Best Trial (ID: {self.best_trial['trial_id']}):")
            print(f"   {self.metric}: {self.best_trial['metric_value']:.4f}")
            print(f"\n   Best Configuration:")

            # Print key hyperparameters
            for param_name in self.search_space.keys():
                keys = param_name.split(".")
                value = self.best_trial["config"]
                for key in keys:
                    value = value[key]
                print(f"      {param_name}: {value}")

        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Hyperparameter Search Script")
    parser.add_argument(
        "--config",
        type=str,
        default="agent4_advanced_finetuning/configs/hyperparam_search.yaml",
        help="Path to hyperparameter search config"
    )
    parser.add_argument(
        "--trials",
        type=int,
        help="Override number of trials"
    )
    args = parser.parse_args()

    # Initialize searcher
    searcher = HyperparameterSearcher(args.config)

    # Override trials if specified
    if args.trials:
        searcher.num_trials = args.trials

    # Run search
    searcher.run_search()

    # Print summary
    searcher.print_summary()

    # Print best config message
    if searcher.best_trial:
        print("Best config found!")
        print(f"Best {searcher.metric}: {searcher.best_trial['metric_value']:.4f}")
    else:
        print("No successful trials completed")


if __name__ == "__main__":
    main()
