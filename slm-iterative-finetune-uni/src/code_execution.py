"""
Sichere Code-Ausführung für Evaluation
========================================

Führt generierten Python-Code in isolierter Umgebung aus und prüft Korrektheit.
"""

import ast
import multiprocessing
import signal
import sys
import traceback
from io import StringIO
from typing import Any, Dict, Optional, Tuple


# ============================================================================
# Timeout-Handler
# ============================================================================

class TimeoutException(Exception):
    """Exception für Code-Timeout."""
    pass


def timeout_handler(signum, frame):
    """Signal-Handler für Timeout."""
    raise TimeoutException("Code execution timed out")


# ============================================================================
# Code-Validierung
# ============================================================================

def check_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Prüft syntaktische Korrektheit von Python-Code.

    Args:
        code: Python-Code als String

    Returns:
        (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Parsing error: {str(e)}"


def has_function_definition(code: str, function_name: Optional[str] = None) -> bool:
    """
    Prüft, ob Code eine Funktionsdefinition enthält.

    Args:
        code: Python-Code
        function_name: Erwarteter Funktionsname (optional)

    Returns:
        True wenn Funktionsdefinition vorhanden
    """
    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if function_name is None or node.name == function_name:
                    return True

        return False

    except:
        return False


# ============================================================================
# Sichere Code-Ausführung
# ============================================================================

def execute_code_safe(
    code: str,
    test_cases: list,
    timeout: int = 5,
    sandbox: bool = True
) -> Dict[str, Any]:
    """
    Führt Code sicher aus und testet mit gegebenen Test-Cases.

    Args:
        code: Zu testender Python-Code
        test_cases: Liste von (input, expected_output) Tupeln
        timeout: Timeout in Sekunden
        sandbox: Ob Sandbox-Modus verwendet werden soll

    Returns:
        Dict mit Ergebnissen:
        {
            "passed": bool,
            "total_tests": int,
            "passed_tests": int,
            "failed_tests": int,
            "error": str (optional),
            "error_type": str (optional),
            "execution_time": float,
            "test_results": list
        }
    """

    # Syntax-Check
    is_valid, syntax_error = check_syntax(code)
    if not is_valid:
        return {
            "passed": False,
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": len(test_cases),
            "error": syntax_error,
            "error_type": "syntax_error",
            "execution_time": 0.0,
            "test_results": []
        }

    # Code ausführen
    if sandbox:
        return _execute_in_sandbox(code, test_cases, timeout)
    else:
        return _execute_direct(code, test_cases, timeout)


def _execute_direct(
    code: str,
    test_cases: list,
    timeout: int
) -> Dict[str, Any]:
    """
    Direkte Ausführung ohne Sandbox (für schnelleres Testing).
    ACHTUNG: Nur für vertrauenswürdigen Code!
    """

    import time

    start_time = time.time()
    test_results = []
    passed_tests = 0

    try:
        # Code ausführen und Funktionen extrahieren
        namespace = {}
        exec(code, namespace)

        # Funktionsnamen finden
        function_names = [
            name for name, obj in namespace.items()
            if callable(obj) and not name.startswith('_')
        ]

        if not function_names:
            return {
                "passed": False,
                "total_tests": len(test_cases),
                "passed_tests": 0,
                "failed_tests": len(test_cases),
                "error": "No callable function found in code",
                "error_type": "no_function",
                "execution_time": time.time() - start_time,
                "test_results": []
            }

        # Erste Funktion verwenden (Konvention in HumanEval)
        func = namespace[function_names[0]]

        # Test-Cases durchlaufen
        for test_input, expected_output in test_cases:
            try:
                # Timeout setzen
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)

                # Funktion aufrufen
                if isinstance(test_input, dict):
                    result = func(**test_input)
                elif isinstance(test_input, (list, tuple)):
                    result = func(*test_input)
                else:
                    result = func(test_input)

                # Timeout zurücksetzen
                signal.alarm(0)

                # Ergebnis prüfen
                passed = result == expected_output

                test_results.append({
                    "input": test_input,
                    "expected": expected_output,
                    "actual": result,
                    "passed": passed,
                    "error": None
                })

                if passed:
                    passed_tests += 1

            except TimeoutException:
                signal.alarm(0)
                test_results.append({
                    "input": test_input,
                    "expected": expected_output,
                    "actual": None,
                    "passed": False,
                    "error": "Timeout"
                })

            except Exception as e:
                signal.alarm(0)
                test_results.append({
                    "input": test_input,
                    "expected": expected_output,
                    "actual": None,
                    "passed": False,
                    "error": str(e)
                })

        execution_time = time.time() - start_time
        total_tests = len(test_cases)
        failed_tests = total_tests - passed_tests

        return {
            "passed": passed_tests == total_tests,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error": None,
            "error_type": None if passed_tests == total_tests else "logic_error",
            "execution_time": execution_time,
            "test_results": test_results
        }

    except Exception as e:
        execution_time = time.time() - start_time
        error_type = type(e).__name__.lower()

        return {
            "passed": False,
            "total_tests": len(test_cases),
            "passed_tests": passed_tests,
            "failed_tests": len(test_cases) - passed_tests,
            "error": str(e),
            "error_type": error_type,
            "execution_time": execution_time,
            "test_results": test_results
        }


def _execute_in_sandbox(
    code: str,
    test_cases: list,
    timeout: int
) -> Dict[str, Any]:
    """
    Führt Code in separatem Prozess aus (Sandbox).
    Sicherer, aber langsamer.
    """

    def _run_in_process(queue, code, test_cases, timeout):
        """Worker-Funktion für Multiprocessing."""
        try:
            result = _execute_direct(code, test_cases, timeout)
            queue.put(result)
        except Exception as e:
            queue.put({
                "passed": False,
                "total_tests": len(test_cases),
                "passed_tests": 0,
                "failed_tests": len(test_cases),
                "error": str(e),
                "error_type": "execution_error",
                "execution_time": 0.0,
                "test_results": []
            })

    # Multiprocessing Queue
    queue = multiprocessing.Queue()

    # Prozess starten
    process = multiprocessing.Process(
        target=_run_in_process,
        args=(queue, code, test_cases, timeout * 2)  # Doppeltes Timeout für Prozess
    )

    process.start()
    process.join(timeout=timeout * 2 + 1)

    # Prozess läuft noch?
    if process.is_alive():
        process.terminate()
        process.join()

        return {
            "passed": False,
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": len(test_cases),
            "error": "Process timeout",
            "error_type": "timeout",
            "execution_time": timeout,
            "test_results": []
        }

    # Ergebnis holen
    if not queue.empty():
        return queue.get()
    else:
        return {
            "passed": False,
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": len(test_cases),
            "error": "Process crashed without result",
            "error_type": "crash",
            "execution_time": 0.0,
            "test_results": []
        }


# ============================================================================
# Code-Analyse
# ============================================================================

def analyze_code_structure(code: str) -> Dict[str, Any]:
    """
    Analysiert Struktur des generierten Codes.

    Returns:
        Dict mit Analyse-Ergebnissen
    """

    try:
        tree = ast.parse(code)

        analysis = {
            "num_functions": 0,
            "num_classes": 0,
            "num_loops": 0,
            "num_conditionals": 0,
            "num_lines": len(code.split('\n')),
            "num_characters": len(code),
            "has_return": False,
            "has_docstring": False,
            "complexity_score": 0
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis["num_functions"] += 1

                # Docstring vorhanden?
                if (ast.get_docstring(node) is not None):
                    analysis["has_docstring"] = True

            elif isinstance(node, ast.ClassDef):
                analysis["num_classes"] += 1

            elif isinstance(node, (ast.For, ast.While)):
                analysis["num_loops"] += 1
                analysis["complexity_score"] += 2

            elif isinstance(node, ast.If):
                analysis["num_conditionals"] += 1
                analysis["complexity_score"] += 1

            elif isinstance(node, ast.Return):
                analysis["has_return"] = True

        return analysis

    except Exception as e:
        return {
            "error": str(e),
            "num_lines": len(code.split('\n')),
            "num_characters": len(code)
        }


# ============================================================================
# HumanEval-spezifische Funktionen
# ============================================================================

def evaluate_humaneval_solution(
    problem: Dict[str, Any],
    generated_code: str,
    timeout: int = 5
) -> Dict[str, Any]:
    """
    Evaluiert Lösung für ein HumanEval-Problem.

    Args:
        problem: Dict mit 'prompt', 'test', 'entry_point'
        generated_code: Generierter Code
        timeout: Timeout in Sekunden

    Returns:
        Evaluation-Ergebnis
    """

    # Test-Code extrahieren
    test_code = problem.get("test", "")

    # Vollständigen Code zusammenbauen
    full_code = generated_code + "\n\n" + test_code

    # Ausführen
    try:
        namespace = {}

        # Timeout setzen
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        exec(full_code, namespace)

        # Timeout zurücksetzen
        signal.alarm(0)

        return {
            "passed": True,
            "error": None,
            "error_type": None
        }

    except TimeoutException:
        signal.alarm(0)
        return {
            "passed": False,
            "error": "Timeout",
            "error_type": "timeout"
        }

    except AssertionError as e:
        signal.alarm(0)
        return {
            "passed": False,
            "error": str(e),
            "error_type": "logic_error"
        }

    except Exception as e:
        signal.alarm(0)
        error_type = type(e).__name__.lower()

        return {
            "passed": False,
            "error": str(e),
            "error_type": error_type
        }
