#!/usr/bin/env python3
"""
Visualisierung von Trainings- und Evaluations-Ergebnissen
===========================================================

Erstellt anschauliche Plots für Lernkurven, Fehlertypen, etc.
"""

import argparse
import os
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from utils import (
    load_config, load_json,
    setup_logging, ensure_dir
)


# Style-Konfiguration
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


# ============================================================================
# Daten laden und vorbereiten
# ============================================================================

def load_all_iteration_data(
    eval_logs_dir: str,
    iterations: List[int]
) -> pd.DataFrame:
    """
    Lädt Evaluations-Daten für alle Iterationen.

    Returns:
        Pandas DataFrame mit allen Metriken
    """

    data = []

    for iteration in iterations:
        eval_file = os.path.join(eval_logs_dir, f"iteration_{iteration}_eval.json")

        if not os.path.exists(eval_file):
            continue

        results = load_json(eval_file)
        summary = results['summary']

        data.append({
            'iteration': iteration,
            'pass_rate': summary['pass_rate'],
            'syntax_valid_rate': summary['syntax_valid_rate'],
            'has_function_rate': summary['has_function_rate'],
            'avg_token_overlap': summary['avg_token_overlap'],
            'avg_generation_time': summary['avg_generation_time'],
            'avg_lines': summary['avg_code_structure']['lines'],
            'avg_loops': summary['avg_code_structure']['loops'],
            'avg_conditionals': summary['avg_code_structure']['conditionals'],
            **{f"error_{k}": v for k, v in summary['error_types'].items()}
        })

    return pd.DataFrame(data)


# ============================================================================
# Lernkurven (matplotlib/seaborn)
# ============================================================================

def plot_learning_curves(df: pd.DataFrame, output_dir: str):
    """Erstellt Lernkurven für Hauptmetriken."""

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Lernkurven über Iterationen', fontsize=16, fontweight='bold')

    # Pass Rate
    axes[0, 0].plot(df['iteration'], df['pass_rate'] * 100, marker='o', linewidth=2, markersize=8)
    axes[0, 0].set_title('Pass Rate (%)', fontweight='bold')
    axes[0, 0].set_xlabel('Iteration')
    axes[0, 0].set_ylabel('Pass Rate (%)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_ylim(0, 105)

    # Syntax-Korrektheit
    axes[0, 1].plot(df['iteration'], df['syntax_valid_rate'] * 100, marker='s',
                     color='green', linewidth=2, markersize=8)
    axes[0, 1].set_title('Syntax-Korrektheit (%)', fontweight='bold')
    axes[0, 1].set_xlabel('Iteration')
    axes[0, 1].set_ylabel('Syntax korrekt (%)')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim(0, 105)

    # Token-Overlap
    axes[1, 0].plot(df['iteration'], df['avg_token_overlap'] * 100, marker='^',
                     color='purple', linewidth=2, markersize=8)
    axes[1, 0].set_title('Token-Overlap mit Referenz (%)', fontweight='bold')
    axes[1, 0].set_xlabel('Iteration')
    axes[1, 0].set_ylabel('Token-Overlap (%)')
    axes[1, 0].grid(True, alpha=0.3)

    # Funktionsdefinitionen
    axes[1, 1].plot(df['iteration'], df['has_function_rate'] * 100, marker='D',
                     color='orange', linewidth=2, markersize=8)
    axes[1, 1].set_title('Hat Funktionsdefinition (%)', fontweight='bold')
    axes[1, 1].set_xlabel('Iteration')
    axes[1, 1].set_ylabel('Funktionsdefinition vorhanden (%)')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_ylim(0, 105)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'learning_curves.png'), dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# Fehlertypen-Entwicklung
# ============================================================================

def plot_error_types(df: pd.DataFrame, output_dir: str):
    """Visualisiert Entwicklung der Fehlertypen."""

    # Fehlertyp-Spalten extrahieren
    error_cols = [col for col in df.columns if col.startswith('error_')]

    if not error_cols:
        return

    fig, ax = plt.subplots(figsize=(15, 8))

    # Stacked Area Chart
    error_data = df[['iteration'] + error_cols].set_index('iteration')
    error_data.columns = [col.replace('error_', '') for col in error_cols]

    error_data.plot(kind='area', stacked=True, alpha=0.7, ax=ax)

    ax.set_title('Fehlertypen-Entwicklung über Iterationen', fontsize=14, fontweight='bold')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Anzahl Fehler')
    ax.legend(title='Fehlertyp', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'error_types_evolution.png'), dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# Code-Struktur Entwicklung
# ============================================================================

def plot_code_structure(df: pd.DataFrame, output_dir: str):
    """Visualisiert Entwicklung der Code-Struktur."""

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Code-Struktur Entwicklung', fontsize=16, fontweight='bold')

    # Zeilen
    axes[0].plot(df['iteration'], df['avg_lines'], marker='o', color='blue', linewidth=2)
    axes[0].set_title('Durchschnittliche Zeilenzahl')
    axes[0].set_xlabel('Iteration')
    axes[0].set_ylabel('Zeilen')
    axes[0].grid(True, alpha=0.3)

    # Schleifen
    axes[1].plot(df['iteration'], df['avg_loops'], marker='s', color='green', linewidth=2)
    axes[1].set_title('Durchschnittliche Schleifen')
    axes[1].set_xlabel('Iteration')
    axes[1].set_ylabel('Anzahl Schleifen')
    axes[1].grid(True, alpha=0.3)

    # Bedingungen
    axes[2].plot(df['iteration'], df['avg_conditionals'], marker='^', color='orange', linewidth=2)
    axes[2].set_title('Durchschnittliche Bedingungen')
    axes[2].set_xlabel('Iteration')
    axes[2].set_ylabel('Anzahl if/else')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'code_structure.png'), dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# Heatmap: Aufgaben x Iterationen
# ============================================================================

def plot_task_heatmap(eval_logs_dir: str, iterations: List[int], output_dir: str):
    """
    Erstellt Heatmap: Welche Aufgaben wurden in welcher Iteration gelöst?
    """

    # Daten sammeln
    task_results = {}

    for iteration in iterations:
        eval_file = os.path.join(eval_logs_dir, f"iteration_{iteration}_eval.json")

        if not os.path.exists(eval_file):
            continue

        results = load_json(eval_file)

        for result in results['results']:
            task_id = result['task_id']
            passed = 1 if result.get('passed', False) else 0

            if task_id not in task_results:
                task_results[task_id] = {}

            task_results[task_id][iteration] = passed

    # DataFrame erstellen
    heatmap_data = pd.DataFrame(task_results).T
    heatmap_data = heatmap_data.sort_index()

    # Plot
    fig, ax = plt.subplots(figsize=(max(12, len(iterations) * 2), max(8, len(task_results) * 0.5)))

    sns.heatmap(
        heatmap_data,
        cmap=['#ff6b6b', '#51cf66'],  # Rot = Fehler, Grün = Erfolg
        cbar_kws={'label': 'Status (0=Fehler, 1=Erfolg)'},
        linewidths=0.5,
        linecolor='gray',
        ax=ax
    )

    ax.set_title('Aufgaben-Erfolg über Iterationen', fontsize=14, fontweight='bold')
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Aufgaben-ID', fontsize=12)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'task_heatmap.png'), dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# Interaktive Dashboards (Plotly)
# ============================================================================

def create_interactive_dashboard(df: pd.DataFrame, output_dir: str):
    """Erstellt interaktives HTML-Dashboard mit Plotly."""

    # Subplot-Figur
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Pass Rate',
            'Syntax-Korrektheit',
            'Token-Overlap',
            'Code-Länge (Zeilen)',
            'Fehlertypen',
            'Generierungszeit'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "scatter"}]
        ]
    )

    # Pass Rate
    fig.add_trace(
        go.Scatter(
            x=df['iteration'],
            y=df['pass_rate'] * 100,
            mode='lines+markers',
            name='Pass Rate',
            line=dict(color='blue', width=3),
            marker=dict(size=10)
        ),
        row=1, col=1
    )

    # Syntax-Korrektheit
    fig.add_trace(
        go.Scatter(
            x=df['iteration'],
            y=df['syntax_valid_rate'] * 100,
            mode='lines+markers',
            name='Syntax-Korrektheit',
            line=dict(color='green', width=3),
            marker=dict(size=10)
        ),
        row=1, col=2
    )

    # Token-Overlap
    fig.add_trace(
        go.Scatter(
            x=df['iteration'],
            y=df['avg_token_overlap'] * 100,
            mode='lines+markers',
            name='Token-Overlap',
            line=dict(color='purple', width=3),
            marker=dict(size=10)
        ),
        row=2, col=1
    )

    # Code-Länge
    fig.add_trace(
        go.Scatter(
            x=df['iteration'],
            y=df['avg_lines'],
            mode='lines+markers',
            name='Zeilen',
            line=dict(color='orange', width=3),
            marker=dict(size=10)
        ),
        row=2, col=2
    )

    # Fehlertypen (Stacked Bar)
    error_cols = [col for col in df.columns if col.startswith('error_')]

    for error_col in error_cols:
        fig.add_trace(
            go.Bar(
                x=df['iteration'],
                y=df[error_col],
                name=error_col.replace('error_', ''),
            ),
            row=3, col=1
        )

    # Generierungszeit
    fig.add_trace(
        go.Scatter(
            x=df['iteration'],
            y=df['avg_generation_time'],
            mode='lines+markers',
            name='Generierungszeit',
            line=dict(color='red', width=3),
            marker=dict(size=10)
        ),
        row=3, col=2
    )

    # Layout
    fig.update_layout(
        title_text="Iteratives Fine-Tuning: Interaktives Dashboard",
        title_font_size=20,
        showlegend=True,
        height=1200,
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="Iteration")

    # Y-Achsen Labels
    fig.update_yaxes(title_text="Pass Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Syntax-Korrektheit (%)", row=1, col=2)
    fig.update_yaxes(title_text="Token-Overlap (%)", row=2, col=1)
    fig.update_yaxes(title_text="Zeilen", row=2, col=2)
    fig.update_yaxes(title_text="Anzahl Fehler", row=3, col=1)
    fig.update_yaxes(title_text="Zeit (s)", row=3, col=2)

    # Speichern
    fig.write_html(os.path.join(output_dir, 'interactive_dashboard.html'))


# ============================================================================
# Delta-Visualisierung
# ============================================================================

def plot_deltas(eval_logs_dir: str, iterations: List[int], output_dir: str):
    """Visualisiert Deltas zwischen Iterationen."""

    deltas = []

    for iteration in iterations[1:]:  # Ab Iteration 1
        delta_file = os.path.join(eval_logs_dir, f"iteration_{iteration}_delta.json")

        if not os.path.exists(delta_file):
            continue

        delta = load_json(delta_file)

        if delta.get('is_baseline'):
            continue

        deltas.append({
            'iteration': iteration,
            'pass_rate_delta': delta['pass_rate']['delta'] * 100,
            'syntax_delta': delta['syntax_valid_rate']['delta'] * 100,
            'newly_passed': delta['num_newly_passed'],
            'newly_failed': delta['num_newly_failed']
        })

    if not deltas:
        return

    df_delta = pd.DataFrame(deltas)

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Verbesserungen zwischen Iterationen', fontsize=16, fontweight='bold')

    # Metriken-Deltas
    ax1 = axes[0]
    x = df_delta['iteration']
    width = 0.35

    ax1.bar(x - width/2, df_delta['pass_rate_delta'], width, label='Pass Rate Δ', color='blue')
    ax1.bar(x + width/2, df_delta['syntax_delta'], width, label='Syntax Δ', color='green')

    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Δ (%)')
    ax1.set_title('Metriken-Veränderungen')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Neu bestanden/fehlgeschlagen
    ax2 = axes[1]
    ax2.bar(x - width/2, df_delta['newly_passed'], width, label='Neu bestanden', color='green')
    ax2.bar(x + width/2, -df_delta['newly_failed'], width, label='Neu fehlgeschlagen', color='red')

    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Anzahl Aufgaben')
    ax2.set_title('Aufgaben-Veränderungen')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'deltas.png'), dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Visualisiert Trainings- und Evaluations-Ergebnisse"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Pfad zur Konfigurationsdatei"
    )

    parser.add_argument(
        "--iterations",
        type=str,
        required=True,
        help="Komma-separierte Liste von Iterationen (z.B. '0,1,2,3')"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output-Verzeichnis (überschreibt config)"
    )

    args = parser.parse_args()

    # Konfiguration laden
    config = load_config(args.config)

    # Logger
    logger = setup_logging(
        log_dir=config['logging']['log_dir'],
        log_file="visualize.log",
        level=config['logging']['level']
    )

    # Iterationen parsen
    iterations = [int(i) for i in args.iterations.split(',')]
    logger.info(f"📊 Visualisiere Iterationen: {iterations}")

    # Output-Verzeichnis
    output_dir = args.output_dir or config['reporting']['reports_dir']
    ensure_dir(output_dir)

    # Daten laden
    logger.info("📚 Lade Evaluations-Daten...")
    eval_logs_dir = config['data']['eval_logs_dir']
    df = load_all_iteration_data(eval_logs_dir, iterations)

    if df.empty:
        logger.error("❌ Keine Daten gefunden!")
        return 1

    logger.info(f"✅ {len(df)} Iterationen geladen")

    # Visualisierungen erstellen
    logger.info("📈 Erstelle Lernkurven...")
    plot_learning_curves(df, output_dir)

    logger.info("📊 Erstelle Fehlertypen-Visualisierung...")
    plot_error_types(df, output_dir)

    logger.info("📊 Erstelle Code-Struktur-Visualisierung...")
    plot_code_structure(df, output_dir)

    logger.info("🔥 Erstelle Task-Heatmap...")
    plot_task_heatmap(eval_logs_dir, iterations, output_dir)

    logger.info("📊 Erstelle Delta-Visualisierung...")
    plot_deltas(eval_logs_dir, iterations, output_dir)

    logger.info("🌐 Erstelle interaktives Dashboard...")
    create_interactive_dashboard(df, output_dir)

    logger.info("\n" + "="*80)
    logger.info("✅ Alle Visualisierungen erstellt!")
    logger.info(f"📁 Output-Verzeichnis: {output_dir}")
    logger.info("="*80 + "\n")

    # Übersicht ausgeben
    print(f"\n✅ Folgende Visualisierungen wurden erstellt:")
    print(f"   - {os.path.join(output_dir, 'learning_curves.png')}")
    print(f"   - {os.path.join(output_dir, 'error_types_evolution.png')}")
    print(f"   - {os.path.join(output_dir, 'code_structure.png')}")
    print(f"   - {os.path.join(output_dir, 'task_heatmap.png')}")
    print(f"   - {os.path.join(output_dir, 'deltas.png')}")
    print(f"   - {os.path.join(output_dir, 'interactive_dashboard.html')}")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
