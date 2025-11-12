# Code-Walkthrough – Wie funktioniert das System?

Dieses Dokument erklärt den **Code** hinter dem iterativen Fine-Tuning System.
Für Studierende, die verstehen wollen: **Wie ist das implementiert?**

---

## 🏗️ System-Architektur

```
┌─────────────────────────────────────────────────────────┐
│                   Workflow pro Iteration                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌─────────────────────────────────┐
         │  1. TRAINING (train.py)         │
         │  - Lade Modell (+ Checkpoint)   │
         │  - Lade Trainingsdaten          │
         │  - Fine-Tune mit LoRA           │
         │  - Speichere neuen Checkpoint   │
         └───────────────┬─────────────────┘
                         │
                         ▼
         ┌─────────────────────────────────┐
         │  2. EVALUATION (eval.py)        │
         │  - Lade trainiertes Modell      │
         │  - Generiere Code für Tests     │
         │  - Führe Code aus (sicher)      │
         │  - Sammle Metriken              │
         └───────────────┬─────────────────┘
                         │
                         ▼
         ┌─────────────────────────────────┐
         │  3. ANALYSE (explain.py)        │
         │  - Delta-Berechnung             │
         │  - Fehlerklassifikation         │
         │  - Erklärungen generieren       │
         │  - Markdown-Report erstellen    │
         └───────────────┬─────────────────┘
                         │
                         ▼
         ┌─────────────────────────────────┐
         │  4. VISUALISIERUNG (visualize.py)│
         │  - Lernkurven plotten           │
         │  - Heatmaps erstellen           │
         │  - Interaktives Dashboard       │
         └─────────────────────────────────┘
```

---

## 📄 Datei-für-Datei Erklärung

### `src/train.py` - Das Trainings-Modul

#### Hauptfunktion: `train_iteration()`

```python
def train_iteration(
    config: Dict[str, Any],
    iteration: int,
    train_data_path: str,
    previous_checkpoint: str = None,
    logger=None
) -> Dict[str, Any]:
```

**Was macht sie?**
1. Lädt Modell (entweder Base-Modell oder Checkpoint der vorherigen Iteration)
2. Lädt Trainingsdaten
3. Konfiguriert Training (Batch-Size, Learning Rate, etc.)
4. Trainiert mit LoRA
5. Speichert neuen Checkpoint

**Schritt-für-Schritt:**

##### Schritt 1: Modell laden

```python
if UNSLOTH_AVAILABLE and config['training']['backend'] == 'unsloth':
    model, tokenizer = load_model_unsloth(config, previous_checkpoint)
else:
    model, tokenizer = load_model_standard(config, previous_checkpoint)
```

**Warum zwei Backends?**
- **Unsloth**: Optimiert, 2x schneller, weniger Speicher
- **Standard Transformers**: Fallback falls Unsloth nicht installiert

**Was passiert intern?** (in `load_model_unsloth`)
```python
# 1. Modell laden (4-bit quantized für Speicher-Effizienz)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    load_in_4bit=True,  # 16GB Modell → 4GB
)

# 2. LoRA-Adapter hinzufügen
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # Rank: Größe der zusätzlichen Matrizen
    target_modules=["q_proj", "k_proj", ...],  # Welche Layer trainieren
)
```

**Was ist LoRA?**
Statt alle Parameter zu ändern (Milliarden!), fügt LoRA kleine Matrizen hinzu:

```
Original: W (1024x1024) = 1M Parameter
LoRA: A (1024x16) + B (16x1024) = 32k Parameter

Speicher-Ersparnis: ~97%!
```

##### Schritt 2: Trainingsdaten laden

```python
train_dataset = load_training_data(
    train_data_path,
    config['data']['prompt_template'],
    tokenizer
)
```

**Was passiert?** (in `load_training_data`)
```python
def format_sample(example):
    # Prompt erstellen
    prompt = "### Instruction:\nSchreibe Python-Code...\n\n### Response:"

    # Mit Lösung kombinieren
    completion = example['canonical_solution']

    # Vollständiger Text für Training
    text = prompt + completion + tokenizer.eos_token

    return {"text": text}
```

**Warum dieses Format?**
Das Modell lernt:
1. "Nach `### Instruction:` kommt die Aufgabe"
2. "Nach `### Response:` soll ich Code generieren"
3. "`<EOS>` bedeutet: Antwort ist fertig"

##### Schritt 3: Training durchführen

```python
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    args=training_args,
    callbacks=[DetailedLoggingCallback(logger, iteration)]
)

train_result = trainer.train()
```

**Was ist SFTTrainer?**
"Supervised Fine-Tuning Trainer" von TRL-Library
- Optimiert für Text-zu-Text Training
- Handhabt Batching, Gradient Accumulation automatisch

**DetailedLoggingCallback:**
```python
class DetailedLoggingCallback(TrainerCallback):
    def on_epoch_begin(self, args, state, control, **kwargs):
        self.logger.info(f"📚 Epoch {int(state.epoch) + 1} beginnt...")

    def on_epoch_end(self, args, state, control, **kwargs):
        self.logger.info(f"✅ Epoch abgeschlossen, Loss: {state.log_history[-1]['loss']:.4f}")
```

**Warum Callbacks?**
Für **transparentes** Training → Studierende sehen, was passiert!

---

### `src/eval.py` - Das Evaluations-Modul

#### Hauptfunktion: `evaluate_single_problem()`

```python
def evaluate_single_problem(
    problem: Dict[str, Any],
    model,
    tokenizer,
    config: Dict[str, Any]
) -> Dict[str, Any]:
```

**Was macht sie?**
1. Generiert Code für eine Aufgabe
2. Prüft Syntax
3. Führt Code aus
4. Sammelt Metriken

**Schritt-für-Schritt:**

##### Schritt 1: Code generieren

```python
generated_code = generate_code(model, tokenizer, prompt, config)
```

**Was passiert intern?**
```python
def generate_code(model, tokenizer, prompt, config):
    # 1. Prompt formatieren
    formatted_prompt = "### Instruction:\n" + prompt + "\n\n### Response:"

    # 2. Tokenisieren (Text → Zahlen)
    inputs = tokenizer(formatted_prompt, return_tensors="pt")

    # 3. Modell generieren lassen
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.2,  # Niedrig = deterministischer
        top_p=0.95,       # Nucleus Sampling
    )

    # 4. Dekodieren (Zahlen → Text)
    generated_text = tokenizer.decode(outputs[0])

    # 5. Nur den Response-Teil extrahieren
    code = generated_text.split("### Response:")[1]

    return code
```

**Was ist `temperature`?**
Kontrolliert "Kreativität":
- `0.1`: Sehr deterministisch, immer gleich
- `1.0`: Mehr Variation, kreativer
- `2.0`: Chaotisch, unvorhersehbar

Für Code wollen wir **niedrige** Temperature (präzise Syntax wichtig).

##### Schritt 2: Syntax prüfen

```python
is_valid_syntax, syntax_error = check_syntax(generated_code)
```

**Implementierung:**
```python
def check_syntax(code: str) -> Tuple[bool, Optional[str]]:
    try:
        ast.parse(code)  # Python's Abstract Syntax Tree Parser
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
```

**Warum AST?**
`ast.parse()` ist Pythons eingebauter Parser - erkennt ALLE Syntax-Fehler.

##### Schritt 3: Code ausführen

```python
execution_result = evaluate_humaneval_solution(
    problem=problem,
    generated_code=generated_code,
    timeout=5
)
```

**Sicherheit ist KRITISCH!**
```python
def evaluate_humaneval_solution(problem, generated_code, timeout):
    # Timeout setzen (Endlosschleifen vermeiden)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        # Code + Test zusammen ausführen
        full_code = generated_code + "\n\n" + problem['test']
        exec(full_code, namespace)

        signal.alarm(0)  # Timeout zurücksetzen
        return {"passed": True, "error": None}

    except TimeoutException:
        return {"passed": False, "error": "Timeout", "error_type": "timeout"}

    except AssertionError as e:
        return {"passed": False, "error": str(e), "error_type": "logic_error"}
```

**Sandbox-Modus** (noch sicherer):
```python
# Code in separatem Prozess ausführen
process = multiprocessing.Process(target=_run_code, args=(code,))
process.start()
process.join(timeout=timeout)

if process.is_alive():
    process.terminate()  # Killen bei Timeout
```

**Warum separater Prozess?**
- Kann sicher gekillt werden
- Keine Auswirkung auf Haupt-Prozess
- Schutz vor bösartigem Code

---

### `src/explain.py` - Das Analyse-Modul

#### Hauptfunktion: `calculate_delta()`

```python
def calculate_delta(
    current_results: Dict[str, Any],
    previous_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
```

**Was macht sie?**
Berechnet **Unterschiede** zwischen zwei Iterationen:

```python
# Pass Rate Delta
pass_rate_delta = curr_summary['pass_rate'] - prev_summary['pass_rate']

# Prozentuale Veränderung
change_pct = (pass_rate_delta / prev_summary['pass_rate'] * 100)
             if prev_summary['pass_rate'] > 0 else float('inf')
```

**Beispiel:**
```python
# Iteration 1: 10% Pass Rate
# Iteration 2: 30% Pass Rate

delta = 30% - 10% = 20 Prozentpunkte
change_pct = (20 / 10) * 100 = 200% relative Verbesserung
```

**Neu bestandene Aufgaben finden:**
```python
newly_passed = []

for task_id in curr_task_results:
    curr_passed = curr_task_results[task_id]['passed']
    prev_passed = prev_task_results[task_id]['passed']

    if curr_passed and not prev_passed:
        newly_passed.append(task_id)
```

**Fehlertyp-Veränderungen:**
```python
error_deltas = {}

for error_type in all_error_types:
    curr_count = curr_errors.get(error_type, 0)
    prev_count = prev_errors.get(error_type, 0)

    error_deltas[error_type] = {
        "current": curr_count,
        "previous": prev_count,
        "delta": curr_count - prev_count  # Negativ = Verbesserung!
    }
```

#### Funktion: `generate_explanations()`

**Was macht sie?**
Erzeugt **menschlich verständliche** Erklärungen aus Deltas:

```python
def generate_explanations(current_results, delta, config):
    explanations = []

    pr = delta['pass_rate']

    if pr['delta'] > 0.1:  # Große Verbesserung
        explanations.append(
            f"🎉 **Großer Fortschritt**: Erfolgsrate stieg um {pr['delta']*100:.1f}% "
            f"Das Modell löst nun {delta['num_newly_passed']} zusätzliche Aufgaben!"
        )

    elif pr['delta'] < 0:  # Verschlechterung!
        explanations.append(
            f"⚠️  **Rückschritt**: Erfolgsrate sank. "
            f"Dies kann auf Overfitting hinweisen."
        )

    # Syntax-Verbesserungen
    if delta['syntax_valid_rate']['delta'] > 0.1:
        explanations.append(
            f"📝 **Syntax-Durchbruch**: Das Modell hat Python-Syntax besser gelernt!"
        )

    return explanations
```

**Warum wichtig?**
Rohdaten sind kryptisch: `{"pass_rate": 0.3, "syntax_valid_rate": 0.85}`
Erklärungen sind lehrreich: "Das Modell hat Syntax gemeistert, kämpft aber noch mit Logik."

#### Funktion: `generate_code_examples()`

**Was macht sie?**
Findet **interessante** Vorher/Nachher-Beispiele:

```python
# Neu bestandene Aufgaben
newly_passed = [
    task_id for task_id in curr_task_results
    if curr_task_results[task_id]['passed']
    and not prev_task_results[task_id]['passed']
]

for task_id in newly_passed[:3]:  # Top 3
    examples.append({
        "type": "newly_passed",
        "task_id": task_id,
        "previous_code": prev_task_results[task_id]['generated_code'],
        "current_code": curr_task_results[task_id]['generated_code'],
        "explanation": "✅ Diese Aufgabe wird nun korrekt gelöst!"
    })
```

**Weitere Kategorien:**
- `improved_but_failing`: Syntax korrigiert, aber Logik noch falsch
- `baseline_failure`: Baseline-Fehler zeigen

---

### `src/visualize.py` - Das Visualisierungs-Modul

#### Funktion: `plot_learning_curves()`

**Was macht sie?**
Erstellt 2x2 Grid mit Lernkurven:

```python
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Pass Rate
axes[0, 0].plot(df['iteration'], df['pass_rate'] * 100, marker='o')
axes[0, 0].set_title('Pass Rate (%)')
axes[0, 0].set_xlabel('Iteration')
axes[0, 0].set_ylabel('Pass Rate (%)')

# Syntax-Korrektheit
axes[0, 1].plot(df['iteration'], df['syntax_valid_rate'] * 100, marker='s')
# ... etc.
```

**Matplotlib vs. Plotly:**
- **Matplotlib**: Statische Bilder (PNG), gut für Papers
- **Plotly**: Interaktiv (HTML), gut für Exploration

#### Funktion: `plot_task_heatmap()`

**Was macht sie?**
Zeigt Matrix: Aufgaben × Iterationen

```python
# Datenstruktur aufbauen
task_results = {}  # {"task_id": {iteration: 0/1}}

for iteration in iterations:
    results = load_json(f"iteration_{iteration}_eval.json")

    for result in results['results']:
        task_id = result['task_id']
        passed = 1 if result['passed'] else 0

        if task_id not in task_results:
            task_results[task_id] = {}

        task_results[task_id][iteration] = passed

# Als DataFrame
heatmap_data = pd.DataFrame(task_results).T

# Heatmap plotten
sns.heatmap(
    heatmap_data,
    cmap=['#ff6b6b', '#51cf66'],  # Rot/Grün
    cbar_kws={'label': 'Status'},
)
```

**Was sieht man?**
- Aufgaben, die in Iteration 2 gelöst werden: Zeile wird grün
- Aufgaben, die nie gelöst werden: Zeile bleibt rot
- Patterns: Mehrere Aufgaben gleichzeitig gelöst → Durchbruch!

#### Funktion: `create_interactive_dashboard()`

**Was macht sie?**
Erstellt HTML-Dashboard mit Plotly:

```python
# Subplot-Figur
fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=('Pass Rate', 'Syntax', ...)
)

# Traces hinzufügen
fig.add_trace(
    go.Scatter(x=df['iteration'], y=df['pass_rate'] * 100, mode='lines+markers'),
    row=1, col=1
)

# Als HTML speichern
fig.write_html('interactive_dashboard.html')
```

**Vorteile interaktiv:**
- Hover für Details
- Zoom
- Traces ein/ausblenden
- Responsive

---

## 🔧 Hilfsfunktionen in `utils.py`

### `set_seed()`
```python
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

**Warum wichtig?**
Für **reproduzierbare** Experimente! Sonst andere Ergebnisse bei jedem Run.

### `classify_error()`
```python
def classify_error(error_message: str, generated_code: str) -> str:
    error_lower = error_message.lower()

    if "syntaxerror" in error_lower:
        return "syntax_error"

    if "timeout" in error_lower:
        return "timeout"

    if not generated_code.strip():
        return "empty_response"

    return "logic_error"
```

**Warum Klassifikation?**
Für aggregierte Statistiken und gezielte Erklärungen.

### `calculate_token_overlap()`
```python
def calculate_token_overlap(generated: str, reference: str) -> float:
    gen_tokens = set(generated.split())
    ref_tokens = set(reference.split())

    overlap = len(gen_tokens & ref_tokens)  # Schnittmenge
    return overlap / len(ref_tokens) if ref_tokens else 0.0
```

**Set-basiert:**
- Ignoriert Reihenfolge
- Ignoriert Wiederholungen
- Schnell

---

## 🐳 Docker Setup

### `Dockerfile_DGX_Spark`

**Layer-für-Layer:**

```dockerfile
# 1. Base Image mit CUDA
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 2. System-Pakete
RUN apt-get update && apt-get install -y \
    python3.10 \
    openjdk-11-jdk  # Für Spark

# 3. PyTorch mit CUDA
RUN pip install torch --index-url https://download.pytorch.org/whl/cu121

# 4. Unsloth
RUN pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# 5. Spark
RUN wget spark-3.5.0.tgz && tar -xzf ... && mv ... /opt/spark
```

**Warum Layer wichtig?**
- Docker cached Layer
- Bei Änderung nur ab geändertem Layer neu bauen
- Schnellere Rebuilds!

### `docker-compose.yml`

**Multi-Node Setup:**
```yaml
services:
  spark-master:
    image: slm-finetune-uni
    environment:
      - SPARK_MODE=master
    ports:
      - "8080:8080"  # UI
      - "7077:7077"  # Master

  spark-worker-1:
    image: slm-finetune-uni
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
```

**Service-Kommunikation:**
```
Worker 1 → spark://spark-master:7077 → Master
Worker 2 → spark://spark-master:7077 → Master
```

**GPU-Mapping:**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0', '1']  # Worker 1 bekommt GPU 0+1
```

---

## 🔄 Workflow-Script: `run_iteration.sh`

**Bash-Tricks:**

### Farben
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

echo -e "${GREEN}✅ Erfolg${NC}"
```

### Error-Handling
```bash
set -e  # Stop bei Fehler

python src/train.py ...

if [ $? -eq 0 ]; then
    echo "Erfolg"
else
    echo "Fehler"
    exit 1
fi
```

### Checkpoint-Detection
```bash
if [ $ITERATION -eq 1 ]; then
    CHECKPOINT_ARG=""  # Keine vorherige Iteration
else
    PREV_ITERATION=$((ITERATION - 1))
    PREV_CHECKPOINT="checkpoints/iteration_${PREV_ITERATION}_model"

    if [ -d "$PREV_CHECKPOINT" ]; then
        CHECKPOINT_ARG="--previous-checkpoint $PREV_CHECKPOINT"
    fi
fi
```

---

## 💾 Datenformate

### Training-Daten (JSON)
```json
[
  {
    "instruction": "Write a function that adds two numbers.",
    "prompt": "def add(a, b):\n    \"\"\"...\"\"\"\n",
    "canonical_solution": "    return a + b\n"
  }
]
```

**Keys:**
- `instruction`: Aufgabenbeschreibung
- `prompt`: Code-Skeleton
- `canonical_solution`: Referenzlösung

### Evaluation-Results (JSON)
```json
{
  "iteration": 1,
  "summary": {
    "pass_rate": 0.3,
    "syntax_valid_rate": 0.85,
    "error_types": {"logic_error": 4, "syntax_error": 2}
  },
  "results": [
    {
      "task_id": "HumanEval/0",
      "passed": true,
      "generated_code": "...",
      "error": null
    }
  ]
}
```

### Delta-Report (JSON)
```json
{
  "pass_rate": {
    "current": 0.3,
    "previous": 0.1,
    "delta": 0.2,
    "change_percent": 200.0
  },
  "newly_passed_tasks": ["HumanEval/3", "HumanEval/7"]
}
```

---

## 🎯 Design-Entscheidungen

### Warum JSON statt CSV?
- **Nested Data**: Code, Errors, Metriken
- **Arrays**: Test-Cases, Error-Types
- **Flexibilität**: Neue Felder einfach hinzufügen

### Warum Markdown-Reports?
- **Lesbar**: Auch ohne Tool
- **Git-Friendly**: Diffs sichtbar
- **Portabel**: Jeder Editor

### Warum Plotly UND Matplotlib?
- **Matplotlib**: Papers, Präsentationen (statisch)
- **Plotly**: Exploration, Debugging (interaktiv)

### Warum LoRA statt Full Fine-Tuning?
- **Speicher**: 4GB statt 40GB
- **Speed**: 2-3x schneller
- **Qualität**: Fast identisch (für unsere Zwecke)

---

## 🧪 Testing & Debugging

### Logging checken
```bash
tail -f logs/train_iteration_1.log
```

### Config validieren
```python
from utils import load_config
config = load_config('config.yaml')
print(config['model']['base_model'])
```

### Einzelne Aufgabe testen
```python
from code_execution import evaluate_humaneval_solution

problem = {...}
code = "def add(a, b): return a + b"

result = evaluate_humaneval_solution(problem, code, timeout=5)
print(result)
```

### GPU-Auslastung monitoren
```bash
watch -n 1 nvidia-smi
```

---

## 📚 Weiterführende Konzepte

### Distributed Training mit DDP
```python
torch.distributed.init_process_group(backend="nccl")
model = DistributedDataParallel(model)
```

**Warum?**
- Training auf mehreren GPUs parallel
- Near-linear Speedup (4 GPUs → 3.5x schneller)

### Gradient Accumulation
```python
# Effektive Batch-Size = 4 * 4 = 16
per_device_train_batch_size=4
gradient_accumulation_steps=4
```

**Warum?**
Simuliert große Batch-Size ohne Speicher-Probleme.

### Mixed Precision Training
```python
bf16=True  # Brain Float 16
```

**Warum?**
- Halbiert Speicherbedarf
- 2-3x schneller auf A100/H100
- Minimal Quality-Loss

---

## 🎓 Übungsaufgaben für Code-Verständnis

1. **Modifiziere `train.py`**: Füge ein Callback hinzu, das nach jeder Epoch eine Test-Prediction macht
2. **Erweitere `eval.py`**: Berechne zusätzliche Metrik (z.B. Cyclomatic Complexity)
3. **Neue Visualisierung**: Erstelle Scatter-Plot von "Code-Länge vs. Pass Rate"
4. **Debugging**: Füge Breakpoints ein und verstehe den Token-Flow
5. **Optimierung**: Caching für wiederholte Evaluationen

---

**Happy Coding! 💻**
