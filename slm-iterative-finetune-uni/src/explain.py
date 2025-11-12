#!/usr/bin/env python3
"""
Report-Generierung mit didaktischen Erklärungen
=================================================

Erstellt ausführliche, menschlich verständliche Reports über:
- Erfolgsraten und Metriken
- Delta-Analysen zwischen Iterationen
- Vorher/Nachher-Beispiele
- Fehlertypen und ihre Bedeutung
"""

import argparse
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils import (
    load_config, load_json, save_json,
    setup_logging, ensure_dir
)


# ============================================================================
# Delta-Analyse zwischen Iterationen
# ============================================================================

def calculate_delta(
    current_results: Dict[str, Any],
    previous_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Berechnet Unterschiede zwischen zwei Iterationen.

    Args:
        current_results: Aktuelle Evaluation
        previous_results: Vorherige Evaluation (oder None)

    Returns:
        Delta-Dict mit Veränderungen
    """

    if previous_results is None:
        return {
            "is_baseline": True,
            "message": "Baseline - keine Vergleichsdaten"
        }

    curr_summary = current_results['summary']
    prev_summary = previous_results['summary']

    # Pass Rate Delta
    pass_rate_delta = curr_summary['pass_rate'] - prev_summary['pass_rate']
    pass_rate_change_pct = (pass_rate_delta / prev_summary['pass_rate'] * 100) if prev_summary['pass_rate'] > 0 else float('inf')

    # Syntax-Korrektheit Delta
    syntax_delta = curr_summary['syntax_valid_rate'] - prev_summary['syntax_valid_rate']

    # Funktionsdefinitionen Delta
    function_delta = curr_summary['has_function_rate'] - prev_summary['has_function_rate']

    # Token-Overlap Delta
    token_overlap_delta = curr_summary['avg_token_overlap'] - prev_summary['avg_token_overlap']

    # Fehlertypen-Veränderungen
    curr_errors = curr_summary['error_types']
    prev_errors = prev_summary['error_types']

    error_deltas = {}
    all_error_types = set(curr_errors.keys()) | set(prev_errors.keys())

    for error_type in all_error_types:
        curr_count = curr_errors.get(error_type, 0)
        prev_count = prev_errors.get(error_type, 0)
        error_deltas[error_type] = {
            "current": curr_count,
            "previous": prev_count,
            "delta": curr_count - prev_count
        }

    # Code-Struktur Deltas
    curr_struct = curr_summary['avg_code_structure']
    prev_struct = prev_summary['avg_code_structure']

    structure_deltas = {
        "lines": curr_struct['lines'] - prev_struct['lines'],
        "loops": curr_struct['loops'] - prev_struct['loops'],
        "conditionals": curr_struct['conditionals'] - prev_struct['conditionals']
    }

    # Neue Erfolge identifizieren
    newly_passed = []
    newly_failed = []

    curr_task_results = {r['task_id']: r for r in current_results['results']}
    prev_task_results = {r['task_id']: r for r in previous_results['results']}

    for task_id in curr_task_results:
        if task_id in prev_task_results:
            curr_passed = curr_task_results[task_id].get('passed', False)
            prev_passed = prev_task_results[task_id].get('passed', False)

            if curr_passed and not prev_passed:
                newly_passed.append(task_id)
            elif not curr_passed and prev_passed:
                newly_failed.append(task_id)

    delta = {
        "is_baseline": False,
        "pass_rate": {
            "current": curr_summary['pass_rate'],
            "previous": prev_summary['pass_rate'],
            "delta": pass_rate_delta,
            "change_percent": pass_rate_change_pct
        },
        "syntax_valid_rate": {
            "current": curr_summary['syntax_valid_rate'],
            "previous": prev_summary['syntax_valid_rate'],
            "delta": syntax_delta
        },
        "has_function_rate": {
            "current": curr_summary['has_function_rate'],
            "previous": prev_summary['has_function_rate'],
            "delta": function_delta
        },
        "token_overlap": {
            "current": curr_summary['avg_token_overlap'],
            "previous": prev_summary['avg_token_overlap'],
            "delta": token_overlap_delta
        },
        "error_types": error_deltas,
        "code_structure": structure_deltas,
        "newly_passed_tasks": newly_passed,
        "newly_failed_tasks": newly_failed,
        "num_newly_passed": len(newly_passed),
        "num_newly_failed": len(newly_failed)
    }

    return delta


# ============================================================================
# Didaktische Erklärungen generieren
# ============================================================================

def generate_explanations(
    current_results: Dict[str, Any],
    delta: Dict[str, Any],
    config: Dict[str, Any]
) -> List[str]:
    """
    Generiert menschlich verständliche Erklärungen.

    Returns:
        Liste von Erklärungstexten
    """

    explanations = []

    if delta.get('is_baseline'):
        explanations.append(
            "🎯 **Baseline-Iteration**: Dies ist die erste Evaluation. "
            "Das Modell wurde noch nicht auf Code-Generierung trainiert."
        )
        return explanations

    # Pass Rate Veränderung
    pr = delta['pass_rate']
    if pr['delta'] > 0.1:
        explanations.append(
            f"🎉 **Großer Fortschritt**: Die Erfolgsrate stieg um {pr['delta']*100:.1f} "
            f"Prozentpunkte (von {pr['previous']*100:.1f}% auf {pr['current']*100:.1f}%). "
            f"Das Modell löst nun {delta['num_newly_passed']} zusätzliche Aufgaben!"
        )
    elif pr['delta'] > 0:
        explanations.append(
            f"✅ **Verbesserung**: Die Erfolgsrate stieg leicht um {pr['delta']*100:.1f} "
            f"Prozentpunkte. {delta['num_newly_passed']} neue Aufgaben werden gelöst."
        )
    elif pr['delta'] < 0:
        explanations.append(
            f"⚠️  **Rückschritt**: Die Erfolgsrate sank um {abs(pr['delta'])*100:.1f} "
            f"Prozentpunkte. {delta['num_newly_failed']} Aufgaben, die vorher funktionierten, "
            f"schlagen nun fehl. Dies kann auf Overfitting oder unpassende Trainingsdaten hinweisen."
        )
    else:
        explanations.append(
            "➡️  **Stagnation**: Die Erfolgsrate blieb unverändert. "
            "Möglicherweise sind mehr/andere Trainingsdaten nötig."
        )

    # Syntax-Verbesserungen
    sr = delta['syntax_valid_rate']
    if sr['delta'] > 0.1:
        explanations.append(
            f"📝 **Syntax-Durchbruch**: Der Anteil syntaktisch korrekter Lösungen stieg um "
            f"{sr['delta']*100:.1f} Prozentpunkte. Das Modell hat Python-Syntax besser gelernt!"
        )
    elif sr['delta'] < -0.1:
        explanations.append(
            f"⚠️  **Syntax-Regression**: Mehr Syntax-Fehler als zuvor ({abs(sr['delta'])*100:.1f}% "
            f"Verschlechterung). Überprüfe Trainingsdaten auf Fehler."
        )

    # Fehlertyp-Veränderungen
    error_improvements = []
    error_regressions = []

    for error_type, data in delta['error_types'].items():
        if data['delta'] < 0:  # Weniger Fehler = gut
            error_improvements.append(f"{error_type} (-{abs(data['delta'])})")
        elif data['delta'] > 0:
            error_regressions.append(f"{error_type} (+{data['delta']})")

    if error_improvements:
        explanations.append(
            f"🔧 **Fehlerreduktion**: Folgende Fehlertypen traten seltener auf: "
            f"{', '.join(error_improvements)}"
        )

    if error_regressions:
        explanations.append(
            f"⚠️  **Neue Fehler**: Folgende Fehlertypen nahmen zu: "
            f"{', '.join(error_regressions)}"
        )

    # Code-Struktur
    struct = delta['code_structure']
    if struct['loops'] > 0.5:
        explanations.append(
            f"🔁 **Schleifen-Fortschritt**: Das Modell generiert nun im Durchschnitt "
            f"{struct['loops']:.1f} mehr Schleifen pro Lösung. Es lernt iterative Muster!"
        )

    if struct['conditionals'] > 0.5:
        explanations.append(
            f"❓ **Bedingungs-Fortschritt**: Mehr if/else-Strukturen werden verwendet "
            f"(Δ: {struct['conditionals']:.1f}). Das Modell lernt Fallunterscheidungen!"
        )

    return explanations


# ============================================================================
# Beispiel-Code-Vergleiche generieren
# ============================================================================

def generate_code_examples(
    current_results: Dict[str, Any],
    previous_results: Optional[Dict[str, Any]],
    max_examples: int = 3
) -> List[Dict[str, Any]]:
    """
    Generiert Vorher/Nachher-Beispiele für besonders interessante Fälle.

    Returns:
        Liste von Beispiel-Dicts
    """

    if previous_results is None:
        # Baseline: Zeige gescheiterte Versuche
        examples = []
        for result in current_results['results'][:max_examples]:
            if not result.get('passed', False):
                examples.append({
                    "type": "baseline_failure",
                    "task_id": result['task_id'],
                    "prompt": result['prompt'][:200] + "..." if len(result['prompt']) > 200 else result['prompt'],
                    "generated_code": result['generated_code'],
                    "error": result.get('error', 'Unknown error'),
                    "explanation": "Baseline: Modell konnte diese Aufgabe noch nicht lösen."
                })
        return examples

    # Iterative: Zeige Verbesserungen
    examples = []

    curr_task_results = {r['task_id']: r for r in current_results['results']}
    prev_task_results = {r['task_id']: r for r in previous_results['results']}

    # Neu bestandene Aufgaben
    newly_passed = [
        task_id for task_id in curr_task_results
        if curr_task_results[task_id].get('passed', False)
        and not prev_task_results.get(task_id, {}).get('passed', False)
    ]

    for task_id in newly_passed[:max_examples]:
        curr = curr_task_results[task_id]
        prev = prev_task_results.get(task_id, {})

        examples.append({
            "type": "newly_passed",
            "task_id": task_id,
            "prompt": curr['prompt'][:200] + "..." if len(curr['prompt']) > 200 else curr['prompt'],
            "previous_code": prev.get('generated_code', ''),
            "current_code": curr['generated_code'],
            "previous_error": prev.get('error'),
            "explanation": "✅ Diese Aufgabe wird nun korrekt gelöst!"
        })

    # Verbleibende Fehler (aber Verbesserungen erkennbar)
    still_failing = [
        task_id for task_id in curr_task_results
        if not curr_task_results[task_id].get('passed', False)
        and task_id in prev_task_results
    ]

    for task_id in still_failing[:max_examples - len(examples)]:
        curr = curr_task_results[task_id]
        prev = prev_task_results[task_id]

        # Nur wenn sich etwas verbessert hat
        curr_syntax = curr.get('syntax_valid', False)
        prev_syntax = prev.get('syntax_valid', False)

        if curr_syntax and not prev_syntax:
            examples.append({
                "type": "improved_but_failing",
                "task_id": task_id,
                "prompt": curr['prompt'][:200] + "..." if len(curr['prompt']) > 200 else curr['prompt'],
                "previous_code": prev.get('generated_code', ''),
                "current_code": curr['generated_code'],
                "previous_error": prev.get('error'),
                "current_error": curr.get('error'),
                "explanation": "📈 Fortschritt: Syntax nun korrekt, aber logischer Fehler verbleibt."
            })

    return examples


# ============================================================================
# Markdown-Report generieren
# ============================================================================

def generate_markdown_report(
    iteration: int,
    current_results: Dict[str, Any],
    delta: Dict[str, Any],
    explanations: List[str],
    examples: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> str:
    """Generiert Markdown-Report."""

    summary = current_results['summary']

    report = f"""# Iteration {iteration} – Evaluations-Report

**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 Zusammenfassung

| Metrik | Wert |
|--------|------|
| **Gesamt-Aufgaben** | {summary['total_problems']} |
| **Bestanden** | {summary['passed']} ({summary['pass_rate']*100:.1f}%) |
| **Syntax korrekt** | {summary['syntax_valid']} ({summary['syntax_valid_rate']*100:.1f}%) |
| **Hat Funktionsdefinition** | {summary['has_function']} ({summary['has_function_rate']*100:.1f}%) |
| **Ø Token-Overlap** | {summary['avg_token_overlap']:.2%} |
| **Ø Generierungszeit** | {summary['avg_generation_time']:.2f}s |

### Code-Struktur (Durchschnitt)

- **Zeilen:** {summary['avg_code_structure']['lines']:.1f}
- **Schleifen:** {summary['avg_code_structure']['loops']:.1f}
- **Bedingungen:** {summary['avg_code_structure']['conditionals']:.1f}

---

## 🔍 Was hat sich verändert?

"""

    # Delta-Metriken
    if not delta.get('is_baseline'):
        pr = delta['pass_rate']
        sr = delta['syntax_valid_rate']

        report += f"""
### Hauptmetriken

| Metrik | Vorher | Nachher | Δ |
|--------|--------|---------|---|
| **Pass Rate** | {pr['previous']*100:.1f}% | {pr['current']*100:.1f}% | {pr['delta']*100:+.1f}% |
| **Syntax-Korrektheit** | {sr['previous']*100:.1f}% | {sr['current']*100:.1f}% | {sr['delta']*100:+.1f}% |

**Neu bestanden:** {delta['num_newly_passed']} Aufgaben
**Neu fehlgeschlagen:** {delta['num_newly_failed']} Aufgaben

"""

    # Erklärungen
    report += "## 🎓 Didaktische Interpretation\n\n"

    for i, explanation in enumerate(explanations, 1):
        report += f"{i}. {explanation}\n\n"

    # Fehlertypen
    report += "## ❌ Fehlertypen-Verteilung\n\n"

    if summary['error_types']:
        report += "| Fehlertyp | Anzahl |\n"
        report += "|-----------|--------|\n"

        for error_type, count in sorted(
            summary['error_types'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            report += f"| `{error_type}` | {count} |\n"

        report += "\n"

        # Fehlertyp-Erklärungen
        report += "### Was bedeuten diese Fehler?\n\n"

        error_explanations = {
            "syntax_error": "**Syntax-Fehler**: Der generierte Code ist syntaktisch ungültig (z.B. falsche Einrückung, fehlende Klammern).",
            "runtime_error": "**Laufzeit-Fehler**: Code ist syntaktisch korrekt, stürzt aber bei Ausführung ab (z.B. TypeError, NameError).",
            "logic_error": "**Logik-Fehler**: Code läuft durch, aber das Ergebnis ist falsch.",
            "timeout": "**Timeout**: Code lief zu lange (Endlosschleife oder ineffizienter Algorithmus).",
            "empty_response": "**Leere Antwort**: Modell generierte keinen Code.",
            "off_topic": "**Off-Topic**: Modell generierte etwas, das kein Python-Code ist."
        }

        for error_type in summary['error_types']:
            if error_type in error_explanations:
                report += f"- {error_explanations[error_type]}\n"

        report += "\n"

    # Code-Beispiele
    if examples:
        report += "## 💡 Beispiele: Vorher vs. Nachher\n\n"

        for i, example in enumerate(examples, 1):
            report += f"### Beispiel {i}: `{example['task_id']}`\n\n"
            report += f"**Aufgabe:**\n```\n{example['prompt']}\n```\n\n"

            if example['type'] == 'baseline_failure':
                report += f"**Generierter Code:**\n```python\n{example['generated_code']}\n```\n\n"
                report += f"**Fehler:** {example['error']}\n\n"
                report += f"_{example['explanation']}_\n\n"

            elif example['type'] == 'newly_passed':
                report += f"**Vorher (Iteration {iteration-1}):**\n```python\n{example['previous_code']}\n```\n"
                if example['previous_error']:
                    report += f"_Fehler: {example['previous_error']}_\n\n"

                report += f"**Nachher (Iteration {iteration}):**\n```python\n{example['current_code']}\n```\n\n"
                report += f"_{example['explanation']}_\n\n"

            elif example['type'] == 'improved_but_failing':
                report += f"**Vorher:**\n```python\n{example['previous_code']}\n```\n"
                report += f"_Fehler: {example['previous_error']}_\n\n"

                report += f"**Nachher:**\n```python\n{example['current_code']}\n```\n"
                report += f"_Fehler: {example['current_error']}_\n\n"
                report += f"_{example['explanation']}_\n\n"

            report += "---\n\n"

    # Lerntipps
    if config['teaching']['generate_tips']:
        report += "## 💭 Lerntipps für Studierende\n\n"

        if delta.get('is_baseline'):
            report += """
1. **Beobachte die Baseline**: Notiere dir, welche Arten von Fehlern das untrainierte Modell macht.
2. **Hypothesen bilden**: Was müsste das Modell lernen, um besser zu werden?
3. **Metriken verstehen**: Pass@1 ist nicht alles – Syntax-Korrektheit und Fehlertypen sind ebenso wichtig!
"""
        else:
            if delta['pass_rate']['delta'] > 0:
                report += "1. **Erfolg analysieren**: Welche Art von Aufgaben wurden neu gelöst? Gibt es ein Muster?\n"

            if delta['num_newly_failed'] > 0:
                report += "2. **Overfitting erkennen**: Warum schlagen vorher funktionierende Aufgaben nun fehl?\n"

            report += "3. **Nächste Schritte**: Welche Fehlertypen dominieren noch? Was sollte als nächstes trainiert werden?\n"

        report += "\n"

    # Footer
    report += "---\n\n"
    report += f"_Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n"

    return report


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generiert ausführlichen Evaluations-Report"
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
        "--compare-with",
        type=int,
        default=None,
        help="Vorherige Iteration zum Vergleichen"
    )

    args = parser.parse_args()

    # Konfiguration laden
    config = load_config(args.config)

    # Logger
    logger = setup_logging(
        log_dir=config['logging']['log_dir'],
        log_file=f"explain_iteration_{args.iteration}.log",
        level=config['logging']['level']
    )

    logger.info(f"\n{'='*80}")
    logger.info(f"Report-Generierung - Iteration {args.iteration}")
    logger.info(f"{'='*80}\n")

    # Aktuelle Ergebnisse laden
    eval_logs_dir = config['data']['eval_logs_dir']
    current_file = os.path.join(eval_logs_dir, f"iteration_{args.iteration}_eval.json")

    if not os.path.exists(current_file):
        logger.error(f"❌ Evaluations-Datei nicht gefunden: {current_file}")
        return 1

    current_results = load_json(current_file)
    logger.info(f"✅ Aktuelle Ergebnisse geladen: {current_file}")

    # Vorherige Ergebnisse laden (falls angegeben)
    previous_results = None
    if args.compare_with is not None:
        previous_file = os.path.join(eval_logs_dir, f"iteration_{args.compare_with}_eval.json")

        if os.path.exists(previous_file):
            previous_results = load_json(previous_file)
            logger.info(f"✅ Vorherige Ergebnisse geladen: {previous_file}")
        else:
            logger.warning(f"⚠️  Vorherige Evaluations-Datei nicht gefunden: {previous_file}")

    # Delta berechnen
    logger.info("📊 Berechne Deltas...")
    delta = calculate_delta(current_results, previous_results)

    # Delta speichern
    delta_file = os.path.join(eval_logs_dir, f"iteration_{args.iteration}_delta.json")
    save_json(delta, delta_file)
    logger.info(f"💾 Delta gespeichert: {delta_file}")

    # Erklärungen generieren
    logger.info("🎓 Generiere Erklärungen...")
    explanations = generate_explanations(current_results, delta, config)

    # Code-Beispiele generieren
    logger.info("💡 Generiere Code-Beispiele...")
    examples = generate_code_examples(
        current_results,
        previous_results,
        max_examples=config['reporting'].get('max_examples_per_type', 3)
    )

    # Markdown-Report generieren
    logger.info("📝 Generiere Markdown-Report...")
    report = generate_markdown_report(
        args.iteration,
        current_results,
        delta,
        explanations,
        examples,
        config
    )

    # Report speichern
    reports_dir = config['reporting']['reports_dir']
    ensure_dir(reports_dir)

    report_file = os.path.join(reports_dir, f"iteration_{args.iteration}_report.md")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"💾 Report gespeichert: {report_file}")
    logger.info("\n" + "="*80)
    logger.info("✅ Report-Generierung abgeschlossen!")
    logger.info("="*80 + "\n")

    # Report auf Console ausgeben (optional)
    print("\n" + report)

    return 0


if __name__ == "__main__":
    exit(main())
