# Quick Start Guide

## Installation

### Option 1: Lokale Umgebung

```bash
# 1. Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. NLTK-Daten herunterladen
python -c "import nltk; nltk.download('punkt')"
```

### Option 2: Docker (für DGX Spark)

```bash
cd docker
docker build -f Dockerfile_DGX_Spark -t slm-finetune-uni .
docker run --gpus all -v $(pwd)/..:/workspace -p 8888:8888 slm-finetune-uni
```

---

## Workflow: Erste Iterationen durchführen

### 1. Baseline evaluieren (Iteration 0)

```bash
# Modell ohne Training evaluieren
python src/eval.py \
    --iteration 0 \
    --model "unsloth/Qwen2.5-Coder-1.5B-Instruct"

# Report generieren
python src/explain.py --iteration 0
```

**Erwartung:** Pass Rate ≈ 0-10%, viele Syntax-Errors

---

### 2. Iteration 1: Erste Trainingsrunde

```bash
# Training
python src/train.py \
    --iteration 1 \
    --train-data data/train_batches/iteration_1_train.json

# Evaluation
python src/eval.py --iteration 1

# Report mit Vergleich zu Baseline
python src/explain.py --iteration 1 --compare-with 0
```

**Erwartung:** Pass Rate ≈ 10-20%, weniger Syntax-Errors

---

### 3. Iteration 2: Zweite Trainingsrunde

```bash
# Training (verwendet Checkpoint von Iteration 1)
python src/train.py \
    --iteration 2 \
    --train-data data/train_batches/iteration_2_train.json \
    --previous-checkpoint checkpoints/iteration_1_model

# Evaluation & Report
python src/eval.py --iteration 2
python src/explain.py --iteration 2 --compare-with 1
```

**Erwartung:** Pass Rate ≈ 20-30%, mehr komplexe Strukturen

---

### 4. Visualisierung

```bash
# Alle bisherigen Iterationen visualisieren
python src/visualize.py --iterations 0,1,2

# Öffne: reports/interactive_dashboard.html
```

---

## Automatisierter Workflow

Verwende das `run_iteration.sh` Skript für kompletten Durchlauf:

```bash
# Iteration 1
./run_iteration.sh 1

# Iteration 2
./run_iteration.sh 2

# etc.
```

Das Skript führt automatisch aus:
1. Training
2. Evaluation
3. Report-Generierung
4. Visualisierung

---

## Jupyter Notebooks

Für explorative Analyse:

```bash
jupyter notebook notebooks/
```

**Notebooks:**
- `01_baseline_exploration.ipynb` – Baseline-Analyse
- `02_iteration_analysis.ipynb` – Iterationsvergleiche (TODO)
- `03_visualization_dashboard.ipynb` – Interaktive Dashboards (TODO)

---

## Typische Probleme & Lösungen

### Problem: CUDA Out of Memory

**Lösung:** Batch-Size in `config.yaml` reduzieren:

```yaml
training:
  per_device_train_batch_size: 2  # statt 4
  gradient_accumulation_steps: 8  # statt 4
```

### Problem: Unsloth nicht verfügbar

**Lösung:** Fallback auf Standard-Transformers (automatisch):

```yaml
training:
  backend: "transformers"  # statt "unsloth"
```

### Problem: PySpark nicht verfügbar

**Lösung:** Sequential Evaluation (automatisch):

```yaml
evaluation:
  use_spark: false
```

---

## Verzeichnisstruktur nach ersten Runs

```
slm-iterative-finetune-uni/
├── checkpoints/
│   ├── iteration_1_model/      # Trainiertes Modell Iteration 1
│   ├── iteration_1_stats.json
│   ├── iteration_2_model/
│   └── iteration_2_stats.json
├── data/
│   └── eval_logs/
│       ├── iteration_0_eval.json
│       ├── iteration_1_eval.json
│       ├── iteration_1_delta.json
│       └── iteration_2_eval.json
├── reports/
│   ├── iteration_0_report.md
│   ├── iteration_1_report.md
│   ├── iteration_2_report.md
│   ├── learning_curves.png
│   ├── error_types_evolution.png
│   └── interactive_dashboard.html
└── logs/
    ├── train_iteration_1.log
    ├── eval_iteration_1.log
    └── explain_iteration_1.log
```

---

## Nächste Schritte für Lehrende

1. **Eigene Trainingsdaten erstellen**
   - Format: `data/train_batches/iteration_X_train.json`
   - Siehe Beispiele in `iteration_1_train.json` und `iteration_2_train.json`

2. **Eigene Test-Aufgaben definieren**
   - Format: HumanEval-kompatibel
   - Siehe `data/humaneval_test_10.json`

3. **Konfiguration anpassen**
   - `config.yaml` bearbeiten
   - Modell, Hyperparameter, Paths, etc.

4. **Reports anpassen**
   - `src/explain.py` bearbeiten für eigene Erklärungen
   - `config.yaml` → `teaching` Sektion

---

## Ressourcen

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [HumanEval Dataset](https://github.com/openai/human-eval)
- [NVIDIA DGX Spark Playbooks](https://github.com/NVIDIA/spark-rapids)
- [Transformers Documentation](https://huggingface.co/docs/transformers)

---

## Support

Bei Fragen oder Problemen:
1. Logs prüfen: `tail -f logs/train_iteration_X.log`
2. Config validieren: `python -c "from utils import load_config; load_config('config.yaml')"`
3. Issues erstellen im Repository
