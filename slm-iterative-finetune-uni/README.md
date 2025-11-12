# Iteratives Fine-Tuning und Evaluation – Lehr- und Vorzeigeprojekt

## 🎓 Didaktisches Ziel

Dieses Projekt demonstriert **Schritt für Schritt**, wie ein Small Language Model (SLM) durch iteratives Fine-Tuning neue Fähigkeiten erlernt – konkret: **Python-Code-Generierung** auf Basis von HumanEval-Aufgaben.

**Besonderheit: Lerntransparenz!**
- Nicht nur Erfolgsraten (0–100%), sondern **detaillierte Veränderungen** in generierten Antworten
- Fehlerarten-Analyse (Syntax vs. Logik vs. Unverständliche Ausgaben)
- Vorher/Nachher-Vergleiche mit konkreten Beispielen
- Anschauliche Reports und Visualisierungen für Studierende

---

## 📚 Lernziele für Studierende

Nach Durchlaufen dieses Projekts verstehen Studierende:

1. **Wie SLMs iterativ lernen**: Von "kann nichts" zu "löst einfache Aufgaben"
2. **Evaluation jenseits von Metriken**: Qualitative Analyse von Modellantworten
3. **Fehlertypen und ihre Bedeutung**: Syntax-Errors vs. Logik-Bugs vs. Kompetenzgrenzen
4. **Delta-Analysen**: Was ändert sich zwischen Iterationen – und warum?
5. **Praktische ML-Workflows**: Training, Evaluation, Reporting in einem realistischen Setup

---

## 🏗️ Projektstruktur

```
slm-iterative-finetune-uni/
│  README.md                 # Diese Datei
│  requirements.txt          # Python-Dependencies
│  config.yaml               # Zentrale Konfiguration
│
├─ docker/
│    Dockerfile_DGX_Spark    # Setup für NVIDIA DGX Spark + Unsloth
│    docker-compose.yml      # Optional: Orchestrierung
│
├─ notebooks/
│    01_baseline_exploration.ipynb     # Initiale Modell-Exploration
│    02_iteration_analysis.ipynb       # Analyse nach jeder Iteration
│    03_visualization_dashboard.ipynb  # Interaktive Dashboards
│
├─ data/
│    humaneval_test_10.json            # 10 Test-Prompts pro Iteration
│    train_batches/                    # Trainingsdaten je Iteration
│      iteration_1_train.json
│      iteration_2_train.json
│      ...
│    eval_logs/                        # Evaluationsergebnisse
│      iteration_1_eval.json
│      iteration_1_delta.json
│      ...
│
├─ src/
│    train.py                # Fine-Tuning (Unsloth/DGX-basiert)
│    eval.py                 # Parallele Evaluation (PySpark)
│    explain.py              # Report-Generierung mit Erklärungen
│    visualize.py            # Plots und Visualisierungen
│    utils.py                # Hilfsfunktionen
│    code_execution.py       # Sichere Code-Ausführung
│
└─ reports/
     iteration_1_report.md   # Ausführlicher Bericht je Iteration
     iteration_2_report.md
     final_summary.md        # Gesamtübersicht
```

---

## 🚀 Schnellstart

### 1. Environment Setup

**Option A: Lokale Umgebung**
```bash
pip install -r requirements.txt
```

**Option B: Docker (für DGX Spark)**
```bash
cd docker
docker build -f Dockerfile_DGX_Spark -t slm-finetune-uni .
docker run --gpus all -v $(pwd)/..:/workspace slm-finetune-uni
```

### 2. Baseline-Evaluation (Phase 0)

```bash
python src/eval.py --iteration 0 --model "unsloth/Qwen2.5-Coder-1.5B-Instruct"
python src/explain.py --iteration 0
```

**Erwartung**: Modell löst 0–10% der Aufgaben, typische Fehler werden dokumentiert.

### 3. Iteratives Training

```bash
# Iteration 1
python src/train.py --iteration 1 --train-data data/train_batches/iteration_1_train.json
python src/eval.py --iteration 1
python src/explain.py --iteration 1 --compare-with 0

# Iteration 2
python src/train.py --iteration 2 --train-data data/train_batches/iteration_2_train.json
python src/eval.py --iteration 2
python src/explain.py --iteration 2 --compare-with 1

# ... und so weiter
```

### 4. Visualisierung

```bash
python src/visualize.py --iterations 0,1,2,3,4,5
```

Oder interaktiv im Jupyter Notebook: `notebooks/02_iteration_analysis.ipynb`

---

## 📊 Was wird gemessen und erklärt?

### Quantitative Metriken
- **Pass@1**: Anteil korrekt gelöster Aufgaben beim ersten Versuch
- **Syntax-Korrektheit**: Ist der generierte Code syntaktisch valide?
- **Token-Overlap**: Wie viel % der Tokens stimmen mit Referenzlösung überein?
- **Durchschnittliche Lösungslänge**: Zeilen/Token pro Antwort

### Qualitative Analysen (WICHTIG!)
- **Fehlertypen-Verteilung**: Syntax vs. Logik vs. Unverständliche Ausgaben
- **Neue Erfolgsmuster**: Welche Aufgabentypen werden erstmals bestanden?
- **Vorher/Nachher-Beispiele**: Konkrete Modellantworten mit Inline-Kommentaren
- **Delta-Reports**: Was hat sich verbessert/verschlechtert zwischen Iterationen?

### Beispiel-Report-Auszug (Iteration 2)

```markdown
## Iteration 2 → 3: Durchbruch bei Schleifen!

**Erfolgsrate**: 10% → 30% (+20 Prozentpunkte)

### Hauptbeobachtungen:
1. **Erstmals korrekte Funktionssignaturen** bei 8/10 Aufgaben (vorher: 4/10)
2. **Verschachtelte Schleifen** werden nun generiert – aber mit Logik-Bugs
3. **Syntax-Errors** reduziert von 60% auf 20%

### Beispiel: Aufgabe "sum_even_numbers"

**Vorher (Iteration 2)**:
```python
def sum_even_numbers(nums):
    # Modell gab nur leeren Funktionskörper zurück
    pass
```

**Nachher (Iteration 3)**:
```python
def sum_even_numbers(nums):
    total = 0
    for num in nums:
        if num % 2 = 0:  # ← Syntax-Error: sollte == sein
            total += num
    return total
```

**Analyse**: Großer Fortschritt! Logik ist korrekt konzipiert, nur Operator-Fehler.
```

---

## 🧠 Integration von NVIDIA DGX Spark & Unsloth

Dieses Projekt nutzt:

1. **Unsloth** für schnelles, speichereffizientes Fine-Tuning
   - 2x schneller als Standard-Transformers
   - Unterstützt QLoRA, Flash Attention 2
   - [Unsloth Documentation](https://github.com/unslothai/unsloth)

2. **NVIDIA DGX Spark Playbooks** für verteiltes Training
   - Multi-GPU Setup mit PyTorch DDP
   - Optimierte Datenmounts und Monitoring
   - Siehe `docker/Dockerfile_DGX_Spark` für Details

### Playbook-spezifische Konfiguration

In `config.yaml`:
```yaml
training:
  backend: "unsloth"  # oder "transformers"
  distributed: true   # für DGX Multi-GPU
  use_flash_attention: true

spark:
  master: "spark://dgx-cluster:7077"
  executor_memory: "32g"
  executor_cores: 8
```

---

## 🎯 Didaktische Highlights

### 1. Fehler als Lernmoment
Reports erklären **warum** bestimmte Fehler auftreten:
- "Das Modell hat noch nicht gelernt, dass `=` vs. `==` unterschiedliche Bedeutungen haben"
- "Verschachtelte Strukturen werden erkannt, aber die Einrückung ist inkonsistent"

### 2. Schrittweise Komplexität
Trainingsdaten je Iteration:
- **Iteration 1**: Simple Funktionen (Addition, String-Verkettung)
- **Iteration 2**: Schleifen und Bedingungen
- **Iteration 3**: Verschachtelte Strukturen
- **Iteration 4**: Rekursion und komplexe Logik

### 3. Interaktive Exploration
Jupyter Notebooks erlauben:
- Manuelles Inspizieren von Modellantworten
- Eigene Prompts testen
- Visualisierungen anpassen

---

## 📖 Weiterführende Ressourcen

- [HumanEval Dataset](https://github.com/openai/human-eval)
- [Unsloth Fine-Tuning Guide](https://github.com/unslothai/unsloth/wiki)
- [NVIDIA DGX Spark Playbooks](https://github.com/NVIDIA/spark-rapids)
- [Paper: "Evaluating Large Language Models Trained on Code"](https://arxiv.org/abs/2107.03374)

---

## 🤝 Beiträge und Feedback

Dieses Projekt ist für Lehrzwecke konzipiert. Verbesserungsvorschläge willkommen!

**Typische Anpassungen für Lehrende**:
- Andere Code-Aufgaben (z.B. JavaScript, SQL)
- Andere Modelle (Llama, CodeGen, etc.)
- Mehr/weniger Iterationen je nach Semesterdauer

---

## 📜 Lizenz

MIT License – frei verwendbar für akademische Zwecke.
