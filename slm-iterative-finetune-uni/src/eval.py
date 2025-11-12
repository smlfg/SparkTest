#!/usr/bin/env python3
"""
Parallele Prompt-Evaluation mit PySpark
=========================================

Evaluiert generierte Code-Lösungen parallel und detailliert.
"""

import argparse
import os
import time
from datetime import datetime
from typing import Dict, List, Any

import torch
from tqdm import tqdm

# PySpark (optional)
try:
    from pyspark.sql import SparkSession
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False
    print("⚠️  PySpark nicht verfügbar - Sequential Execution")

# Transformers
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    from transformers import AutoModelForCausalLM, AutoTokenizer

# Eigene Module
from utils import (
    load_config, load_json, save_json,
    setup_logging, set_seed, print_gpu_info,
    get_checkpoint_path, ensure_dir,
    extract_code_from_response,
    calculate_token_overlap,
    classify_error
)
from code_execution import (
    check_syntax,
    has_function_definition,
    evaluate_humaneval_solution,
    analyze_code_structure
)


# ============================================================================
# Modell laden
# ============================================================================

def load_model_for_inference(model_path: str, config: Dict[str, Any]):
    """Lädt Modell für Inference."""

    logger = setup_logging()
    logger.info(f"📦 Lade Modell: {model_path}")

    if UNSLOTH_AVAILABLE and config['training']['backend'] == 'unsloth':
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_path,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)  # Inference-Modus
        logger.info("✅ Modell mit Unsloth geladen (Inference-Modus)")
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        model.eval()
        logger.info("✅ Modell mit Transformers geladen")

    return model, tokenizer


# ============================================================================
# Code-Generierung
# ============================================================================

def generate_code(
    model,
    tokenizer,
    prompt: str,
    config: Dict[str, Any]
) -> str:
    """
    Generiert Code für gegebenen Prompt.

    Args:
        model: Modell
        tokenizer: Tokenizer
        prompt: Problem-Beschreibung
        config: Konfiguration

    Returns:
        Generierter Code
    """

    eval_config = config['evaluation']

    # Prompt formatieren
    formatted_prompt = config['data']['prompt_template'].format(
        problem_description=prompt
    )

    # Tokenisieren
    inputs = tokenizer(
        formatted_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    ).to(model.device)

    # Generieren
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=eval_config['max_new_tokens'],
            temperature=eval_config['temperature'],
            top_p=eval_config['top_p'],
            do_sample=eval_config['do_sample'],
            pad_token_id=tokenizer.eos_token_id
        )

    # Dekodieren
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Nur den generierten Teil (ohne Prompt)
    if formatted_prompt in generated_text:
        generated_code = generated_text.split(formatted_prompt)[1]
    else:
        generated_code = generated_text

    # Code extrahieren
    generated_code = extract_code_from_response(generated_code)

    return generated_code


# ============================================================================
# Einzelne Aufgabe evaluieren
# ============================================================================

def evaluate_single_problem(
    problem: Dict[str, Any],
    model,
    tokenizer,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluiert ein einzelnes Problem.

    Args:
        problem: Problem-Dict mit 'prompt', 'test', 'canonical_solution', etc.
        model: Modell
        tokenizer: Tokenizer
        config: Konfiguration

    Returns:
        Evaluations-Ergebnis
    """

    problem_id = problem.get('task_id', problem.get('id', 'unknown'))
    prompt = problem.get('prompt', '')
    canonical_solution = problem.get('canonical_solution', '')

    # Code generieren
    start_time = time.time()
    generated_code = generate_code(model, tokenizer, prompt, config)
    generation_time = time.time() - start_time

    # Syntax-Check
    is_valid_syntax, syntax_error = check_syntax(generated_code)

    # Funktionsdefinition vorhanden?
    has_function = has_function_definition(generated_code)

    # Code-Struktur analysieren
    structure = analyze_code_structure(generated_code)

    # Tests ausführen
    if 'test' in problem:
        execution_result = evaluate_humaneval_solution(
            problem=problem,
            generated_code=generated_code,
            timeout=config['evaluation']['code_timeout']
        )
    else:
        execution_result = {
            "passed": False,
            "error": "No test provided",
            "error_type": "no_test"
        }

    # Fehlertyp klassifizieren
    if not execution_result['passed']:
        error_msg = execution_result.get('error', '')
        error_type = classify_error(error_msg, generated_code)
    else:
        error_type = None

    # Token-Overlap mit Referenzlösung
    token_overlap = calculate_token_overlap(generated_code, canonical_solution)

    # Ergebnis zusammenstellen
    result = {
        "task_id": problem_id,
        "prompt": prompt,
        "generated_code": generated_code,
        "canonical_solution": canonical_solution,
        "passed": execution_result['passed'],
        "syntax_valid": is_valid_syntax,
        "has_function": has_function,
        "error": execution_result.get('error'),
        "error_type": error_type,
        "generation_time": generation_time,
        "token_overlap": token_overlap,
        "code_structure": structure,
        "timestamp": datetime.now().isoformat()
    }

    return result


# ============================================================================
# Batch-Evaluation (Sequential)
# ============================================================================

def evaluate_sequential(
    problems: List[Dict[str, Any]],
    model,
    tokenizer,
    config: Dict[str, Any],
    logger
) -> List[Dict[str, Any]]:
    """Evaluiert Probleme sequenziell."""

    logger.info(f"🔄 Sequential Evaluation von {len(problems)} Problemen...")

    results = []

    for problem in tqdm(problems, desc="Evaluating"):
        try:
            result = evaluate_single_problem(problem, model, tokenizer, config)
            results.append(result)
        except Exception as e:
            logger.error(f"Fehler bei {problem.get('task_id', 'unknown')}: {str(e)}")
            results.append({
                "task_id": problem.get('task_id', 'unknown'),
                "error": str(e),
                "error_type": "evaluation_error"
            })

    return results


# ============================================================================
# Batch-Evaluation (Spark)
# ============================================================================

def evaluate_with_spark(
    problems: List[Dict[str, Any]],
    model_path: str,
    config: Dict[str, Any],
    logger
) -> List[Dict[str, Any]]:
    """
    Evaluiert Probleme parallel mit Spark.

    HINWEIS: In der Praxis benötigt man hier Broadcast-Variables
    für das Modell oder Model-Serving-Infrastruktur.
    Für Lehrzwecke demonstriert dies das Prinzip.
    """

    if not SPARK_AVAILABLE:
        logger.warning("Spark nicht verfügbar - falle zurück auf Sequential")
        # Modell lokal laden
        model, tokenizer = load_model_for_inference(model_path, config)
        return evaluate_sequential(problems, model, tokenizer, config, logger)

    logger.info(f"⚡ Spark Evaluation von {len(problems)} Problemen...")

    eval_config = config['evaluation']

    # Spark Session
    spark = SparkSession.builder \
        .appName("SLM_CodeEval") \
        .master(eval_config.get('spark_master', 'local[*]')) \
        .config("spark.executor.memory", eval_config.get('executor_memory', '8g')) \
        .config("spark.executor.cores", eval_config.get('executor_cores', 2)) \
        .getOrCreate()

    # RDD erstellen
    problems_rdd = spark.sparkContext.parallelize(problems)

    def evaluate_partition(partition):
        """
        Evaluiert Partition von Problemen.
        Lädt Modell einmal pro Executor.
        """
        # Modell pro Worker laden (nur einmal pro Partition)
        from eval import load_model_for_inference, evaluate_single_problem

        model, tokenizer = load_model_for_inference(model_path, config)

        results = []
        for problem in partition:
            try:
                result = evaluate_single_problem(problem, model, tokenizer, config)
                results.append(result)
            except Exception as e:
                results.append({
                    "task_id": problem.get('task_id', 'unknown'),
                    "error": str(e),
                    "error_type": "evaluation_error"
                })

        return results

    # Parallel evaluieren
    results = problems_rdd.mapPartitions(evaluate_partition).collect()

    spark.stop()

    return results


# ============================================================================
# Evaluation zusammenfassen
# ============================================================================

def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Berechnet Zusammenfassung der Evaluations-Ergebnisse."""

    total = len(results)
    passed = sum(1 for r in results if r.get('passed', False))
    syntax_valid = sum(1 for r in results if r.get('syntax_valid', False))
    has_function = sum(1 for r in results if r.get('has_function', False))

    # Fehlertypen zählen
    error_types = {}
    for r in results:
        error_type = r.get('error_type')
        if error_type:
            error_types[error_type] = error_types.get(error_type, 0) + 1

    # Durchschnittliche Metriken
    avg_generation_time = sum(r.get('generation_time', 0) for r in results) / total if total > 0 else 0
    avg_token_overlap = sum(r.get('token_overlap', 0) for r in results) / total if total > 0 else 0

    # Code-Struktur Durchschnitte
    avg_lines = sum(r.get('code_structure', {}).get('num_lines', 0) for r in results) / total if total > 0 else 0
    avg_loops = sum(r.get('code_structure', {}).get('num_loops', 0) for r in results) / total if total > 0 else 0
    avg_conditionals = sum(r.get('code_structure', {}).get('num_conditionals', 0) for r in results) / total if total > 0 else 0

    summary = {
        "total_problems": total,
        "passed": passed,
        "pass_rate": passed / total if total > 0 else 0,
        "syntax_valid": syntax_valid,
        "syntax_valid_rate": syntax_valid / total if total > 0 else 0,
        "has_function": has_function,
        "has_function_rate": has_function / total if total > 0 else 0,
        "error_types": error_types,
        "avg_generation_time": avg_generation_time,
        "avg_token_overlap": avg_token_overlap,
        "avg_code_structure": {
            "lines": avg_lines,
            "loops": avg_loops,
            "conditionals": avg_conditionals
        }
    }

    return summary


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Evaluiert Modell auf Code-Generierungs-Aufgaben"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Pfad zur Konfigurationsdatei"
    )

    parser.add_argument(
        "--iteration",
        type=int,
        required=True,
        help="Iterations-Nummer"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Modell-Pfad (überschreibt auto-detection)"
    )

    parser.add_argument(
        "--test-file",
        type=str,
        default=None,
        help="Test-Datei (überschreibt config)"
    )

    parser.add_argument(
        "--use-spark",
        action="store_true",
        help="Verwende Spark für parallele Evaluation"
    )

    args = parser.parse_args()

    # Konfiguration laden
    config = load_config(args.config)

    # Seed setzen
    set_seed(config.get('seed', 42))

    # Logger
    logger = setup_logging(
        log_dir=config['logging']['log_dir'],
        log_file=f"eval_iteration_{args.iteration}.log",
        level=config['logging']['level']
    )

    logger.info(f"\n{'='*80}")
    logger.info(f"Evaluation - Iteration {args.iteration}")
    logger.info(f"{'='*80}\n")

    # GPU-Info
    print_gpu_info()

    # Modell-Pfad bestimmen
    if args.model:
        model_path = args.model
    elif args.iteration == 0:
        model_path = config['model']['base_model']
    else:
        model_path = get_checkpoint_path(
            config['model']['checkpoint_dir'],
            args.iteration,
            "model"
        )

    logger.info(f"📦 Modell: {model_path}")

    # Test-Probleme laden
    test_file = args.test_file or config['evaluation']['test_file']
    logger.info(f"📚 Lade Test-Probleme: {test_file}")

    problems = load_json(test_file)
    logger.info(f"✅ {len(problems)} Probleme geladen")

    # Evaluation durchführen
    use_spark = args.use_spark or config['evaluation'].get('use_spark', False)

    if use_spark and SPARK_AVAILABLE:
        results = evaluate_with_spark(problems, model_path, config, logger)
    else:
        model, tokenizer = load_model_for_inference(model_path, config)
        results = evaluate_sequential(problems, model, tokenizer, config, logger)

    # Zusammenfassung
    summary = summarize_results(results)

    logger.info("\n" + "="*80)
    logger.info("📊 Evaluations-Ergebnisse:")
    logger.info("="*80)
    logger.info(f"Gesamt: {summary['total_problems']}")
    logger.info(f"Bestanden: {summary['passed']} ({summary['pass_rate']*100:.1f}%)")
    logger.info(f"Syntax korrekt: {summary['syntax_valid']} ({summary['syntax_valid_rate']*100:.1f}%)")
    logger.info(f"Hat Funktion: {summary['has_function']} ({summary['has_function_rate']*100:.1f}%)")
    logger.info(f"\nFehlertypen:")
    for error_type, count in summary['error_types'].items():
        logger.info(f"  {error_type}: {count}")
    logger.info("="*80 + "\n")

    # Ergebnisse speichern
    output_dir = config['data']['eval_logs_dir']
    ensure_dir(output_dir)

    results_file = os.path.join(output_dir, f"iteration_{args.iteration}_eval.json")
    save_json({
        "iteration": args.iteration,
        "model_path": model_path,
        "summary": summary,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }, results_file)

    logger.info(f"💾 Ergebnisse gespeichert: {results_file}")
    logger.info("✅ Evaluation abgeschlossen!")

    return 0


if __name__ == "__main__":
    exit(main())
