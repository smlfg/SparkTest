# Tutorial für Studierende – Iteratives Fine-Tuning verstehen

## 🎯 Was lerne ich in diesem Projekt?

Nach Durcharbeiten dieses Projekts verstehst du:

1. **Wie Machine Learning Modelle iterativ lernen**
   - Nicht "auf einmal perfekt", sondern Schritt für Schritt
   - Wie Trainingsdaten die Fähigkeiten beeinflussen

2. **Wie man ML-Modelle evaluiert**
   - Nicht nur "richtig oder falsch"
   - Qualitative Analyse: Was verbessert sich? Welche Fehlertypen?

3. **Praktische ML-Engineering-Skills**
   - Training-Pipelines
   - Evaluation-Frameworks
   - Visualisierung und Reporting

4. **Code-Generierung mit LLMs**
   - Wie SLMs Python-Code lernen
   - Typische Fehler und wie man sie behebt

---

## 📚 Konzepte Schritt für Schritt

### Phase 1: Baseline verstehen

#### Was passiert?
Du evaluierst ein **untrainiertes** Modell auf Code-Generierungs-Aufgaben.

#### Warum wichtig?
Um zu sehen, was das Modell **schon kann** (oft: nichts) und wo die Reise hingeht.

#### Typische Beobachtungen:
- **Pass Rate: 0-10%** - Fast alle Aufgaben scheitern
- **Syntax-Errors: 60-80%** - Modell kennt Python-Syntax nicht
- **Fehlertypen**:
  - Leere Antworten (`pass` Statement)
  - Off-Topic (kein Python-Code)
  - Syntax-Chaos (fehlende Klammern, falsche Einrückung)

#### Code-Beispiel (typische Baseline-Ausgabe):
```python
# Aufgabe: Schreibe eine Funktion, die zwei Zahlen addiert
def add(a, b):
    # Modell gibt oft einfach zurück:
    pass
```

**Warum?** Das Basis-Modell wurde auf generellen Text trainiert, nicht speziell auf Code.

---

### Phase 2: Erste Trainingsrunde (Iteration 1)

#### Was passiert?
Das Modell wird auf **einfachen Python-Funktionen** trainiert:
- Addition, Multiplikation
- String-Verkettung
- Einfache if/else

#### Trainingsdaten-Struktur:
```json
{
  "instruction": "Write a Python function that adds two numbers.",
  "prompt": "def add(a, b):\n    \"\"\"Return the sum of two numbers.\"\"\"\n",
  "canonical_solution": "    return a + b\n"
}
```

**Was lernt das Modell?**
1. **Funktions-Syntax**: `def name(params):`
2. **Return-Statement**: `return result`
3. **Grundlegende Operatoren**: `+`, `*`, `==`

#### Erwartete Verbesserungen:
- Pass Rate: 0% → 10-20%
- Syntax-Korrektheit: 20% → 60%
- **Neue Fähigkeiten**:
  - Funktionsdefinitionen werden generiert
  - Einfache Return-Statements funktionieren

#### Typisches Beispiel nach Iteration 1:
```python
# Vorher (Iteration 0):
def add(a, b):
    pass

# Nachher (Iteration 1):
def add(a, b):
    return a + b  # ✅ Korrekt!
```

---

### Phase 3: Zweite Trainingsrunde (Iteration 2)

#### Was passiert?
Training auf **komplexeren Strukturen**:
- Schleifen (`for`, `while`)
- Bedingungen (`if/elif/else`)
- Listen-Operationen

#### Trainingsdaten-Beispiel:
```json
{
  "instruction": "Write a Python function that sums all elements in a list.",
  "prompt": "def sum_list(numbers):\n    \"\"\"Sum all elements.\"\"\"\n",
  "canonical_solution": "    total = 0\n    for num in numbers:\n        total += num\n    return total\n"
}
```

**Was lernt das Modell?**
1. **For-Schleifen**: Iterieren über Listen
2. **Akkumulatoren**: Variable hochzählen
3. **Verschachtelte Logik**: If in Schleife

#### Erwartete Verbesserungen:
- Pass Rate: 20% → 30-40%
- **Neue Fehlertypen**:
  - Logik-Fehler (Schleife korrekt, aber Rückgabewert falsch)
  - Off-by-One Errors
  - Vergessene Edge Cases (leere Liste)

#### Typisches Beispiel:
```python
# Iteration 1 (scheitert bei Schleifen):
def count_evens(numbers):
    return numbers % 2 == 0  # ❌ Syntax/Logik-Error

# Iteration 2 (lernt Schleifen):
def count_evens(numbers):
    count = 0
    for num in numbers:
        if num % 2 = 0:  # ⚠️ Syntax-Error (sollte == sein)
            count += 1
    return count

# Iteration 3 (korrigiert):
def count_evens(numbers):
    count = 0
    for num in numbers:
        if num % 2 == 0:  # ✅
            count += 1
    return count
```

**Wichtige Beobachtung**: Das Modell lernt die **Struktur** (Schleife), macht aber noch **Detail-Fehler** (Operator).

---

## 🔍 Metriken verstehen

### Pass@1 (Pass Rate)
**Was ist das?**
Anteil der Aufgaben, die beim ersten Versuch korrekt gelöst werden.

**Beispiel:**
- 10 Aufgaben
- 3 korrekt gelöst
- Pass@1 = 30%

**Warum wichtig?**
Zeigt die **Gesamt-Kompetenz** des Modells.

**Aber Vorsicht:**
Pass@1 allein sagt nichts über **Fortschritt** bei einzelnen Aspekten!

### Syntax-Korrektheit
**Was ist das?**
Kann der generierte Code überhaupt **ausgeführt** werden (ohne Syntax-Error)?

**Beispiel:**
```python
# Syntax-korrekt (aber logisch falsch):
def add(a, b):
    return a - b  # Subtrahiert statt addiert

# Syntax-NICHT-korrekt:
def add(a, b)
    return a + b  # Fehlt: Doppelpunkt
```

**Warum wichtig?**
Syntax-Korrektheit ist **Voraussetzung** für Logik-Tests. Wenn Syntax falsch ist, stürzt das Programm sofort ab.

**Typische Entwicklung:**
- Iteration 0: 20% syntax-korrekt
- Iteration 1: 60% syntax-korrekt
- Iteration 2: 85% syntax-korrekt

### Token-Overlap
**Was ist das?**
Wie viele "Wörter" (Tokens) des generierten Codes stimmen mit der Referenzlösung überein?

**Beispiel:**
```python
# Referenz:
return a + b

# Generiert:
return a + b  # 100% Overlap

# Generiert:
result = a + b
return result  # ~50% Overlap (andere Wörter, aber richtig)
```

**Warum wichtig?**
Hoher Token-Overlap bedeutet oft **ähnlicher Lösungsansatz** wie Referenz.

**Aber Vorsicht:**
Niedriger Overlap heißt nicht unbedingt "falsch" - es könnte eine **alternative** Lösung sein!

### Code-Struktur-Metriken

#### Durchschnittliche Zeilen
Wie lang sind die generierten Lösungen?

**Entwicklung:**
- Iteration 0: 2 Zeilen (nur `pass`)
- Iteration 1: 3-4 Zeilen (einfache Returns)
- Iteration 2: 6-8 Zeilen (Schleifen)

#### Anzahl Schleifen/Bedingungen
Wie viele `for`/`while`/`if` werden verwendet?

**Warum interessant?**
Zeigt, ob das Modell **komplexe Strukturen** lernt.

---

## 📊 Reports lesen und verstehen

### Beispiel-Report-Auszug:

```markdown
## 🔍 Was hat sich verändert?

| Metrik | Vorher | Nachher | Δ |
|--------|--------|---------|---|
| Pass Rate | 10.0% | 30.0% | +20.0% |
| Syntax-Korrektheit | 60.0% | 85.0% | +25.0% |

Neu bestanden: 2 Aufgaben
Neu fehlgeschlagen: 0 Aufgaben
```

**Was bedeutet das?**
1. **Pass Rate +20%**: 2 von 10 zusätzlichen Aufgaben gelöst
2. **Syntax +25%**: Das Modell macht weniger Syntax-Fehler
3. **0 Regressions**: Keine vorher funktionierenden Aufgaben gehen kaputt ✅

### Fehlertypen-Tabelle:

```markdown
| Fehlertyp | Anzahl |
|-----------|--------|
| logic_error | 4 |
| syntax_error | 2 |
| timeout | 1 |
```

**Interpretation:**
- **4 Logik-Fehler**: Syntax OK, aber Ergebnis falsch
  → Modell kennt Struktur, aber Details noch nicht
- **2 Syntax-Fehler**: Noch nicht alle Syntax-Regeln gelernt
- **1 Timeout**: Wahrscheinlich Endlosschleife

**Lerntipp:**
Wenn Syntax-Fehler abnehmen, aber Logik-Fehler zunehmen, ist das **Fortschritt**! Das Modell hat Phase 1 (Syntax) gemeistert und ist bei Phase 2 (Logik).

### Vorher/Nachher-Beispiele:

```markdown
### Beispiel 1: `HumanEval/3`

**Vorher (Iteration 1):**
```python
def below_zero(operations):
    pass
```
_Fehler: Empty response_

**Nachher (Iteration 2):**
```python
def below_zero(operations):
    balance = 0
    for op in operations:
        balance += op
        if balance < 0:
            return True
    return False
```
_✅ Diese Aufgabe wird nun korrekt gelöst!_
```

**Was lerne ich daraus?**
1. Iteration 1: Modell konnte gar nichts
2. Iteration 2: Modell hat gelernt:
   - Schleife über Liste
   - Akkumulator (`balance`)
   - Bedingte Rückgabe
   - Früher Return vs. finaler Return

---

## 🛠️ Praktische Aufgaben für Studierende

### Aufgabe 1: Baseline analysieren
1. Führe Baseline-Evaluation aus
2. Öffne `reports/iteration_0_report.md`
3. Beantworte:
   - Welche Fehlertypen dominieren?
   - Gibt es überhaupt Aufgaben, die bestanden werden?
   - Was müsste das Modell lernen?

### Aufgabe 2: Erste Verbesserungen beobachten
1. Trainiere Iteration 1
2. Vergleiche Report Iteration 0 vs. 1
3. Beantworte:
   - Welche Metriken verbessern sich am meisten?
   - Welche Aufgaben werden neu gelöst?
   - Gibt es unerwartete Verschlechterungen?

### Aufgabe 3: Trainingsdaten designen
1. Öffne `data/train_batches/iteration_1_train.json`
2. Analysiere: Was wird trainiert?
3. Erstelle eigene Trainingsdaten für Iteration 3:
   - Welche Fähigkeiten sollen gelernt werden?
   - Wie viele Beispiele sind nötig?
   - Welche Schwierigkeit?

### Aufgabe 4: Visualisierungen interpretieren
1. Öffne `reports/interactive_dashboard.html`
2. Beobachte:
   - Welche Metriken korrelieren?
   - Gibt es Plateaus? Warum?
   - Welche Iteration brachte den größten Sprung?

### Aufgabe 5: Fehleranalyse
1. Öffne `data/eval_logs/iteration_2_eval.json`
2. Suche 3 Aufgaben mit `"passed": false`
3. Analysiere:
   - Was ging schief?
   - Klassifiziere Fehlertyp
   - Was müsste das Modell noch lernen?

---

## 💡 Häufige Fragen

### F: Warum steigt die Pass Rate manchmal nicht?
**A:** Mehrere Gründe:
1. **Falsches Training**: Trainingsdaten passen nicht zu Test-Aufgaben
2. **Overfitting**: Modell lernt Trainingsdaten auswendig, generalisiert nicht
3. **Plateau**: Modell hat aktuelles Niveau erreicht, braucht neue Lernstrategie
4. **Regression**: Neue Trainingsdaten "überschreiben" alte Fähigkeiten

### F: Was ist besser: Hohe Pass Rate oder hohe Syntax-Korrektheit?
**A:** Kommt auf Phase an:
- **Früh** (Iteration 1-2): Syntax-Korrektheit wichtiger → Fundament
- **Später** (Iteration 3+): Pass Rate wichtiger → Echte Fähigkeiten

### F: Kann ein Modell "verlernen"?
**A:** Ja! Wenn neue Trainingsdaten zu spezialisiert sind, können alte Fähigkeiten schwinden.
**Lösung:** Trainingsdaten aus vorherigen Iterationen **beimischen**.

### F: Wie viele Iterationen sind nötig?
**A:** Hängt ab von:
- Ziel-Kompetenz (50% Pass Rate? 90%?)
- Modellgröße (größere Modelle lernen schneller)
- Trainingsdaten-Qualität

**Typisch:** 5-10 Iterationen für signifikante Verbesserung.

### F: Warum parallele Evaluation mit Spark?
**A:** Geschwindigkeit!
- **Sequential**: 10 Aufgaben à 5s = 50s
- **Parallel (4 Cores)**: 10 Aufgaben = ~15s

Bei 100+ Aufgaben macht das einen großen Unterschied.

---

## 🎓 Weiterführende Konzepte

### Fine-Tuning vs. Training from Scratch
**Fine-Tuning** (was wir machen):
- Startet mit vortrainiertem Modell
- Anpassung auf spezifische Aufgabe
- Schneller, weniger Daten nötig

**From Scratch:**
- Startet mit zufälligen Gewichten
- Braucht riesige Datenmengen
- Nur für große Organisationen praktikabel

### LoRA (Low-Rank Adaptation)
In `config.yaml` siehst du:
```yaml
lora:
  r: 16
  lora_alpha: 16
```

**Was ist das?**
Statt **alle** Modell-Parameter zu trainieren (Milliarden!), trainiert LoRA nur **zusätzliche kleine Matrizen**.

**Vorteil:**
- Viel weniger Speicher
- Schnelleres Training
- Gleichwertiges Ergebnis

### Prompt Engineering für Training
Die Struktur der Trainingsdaten ist wichtig:
```
### Instruction:
<Aufgabenstellung>

### Response:
<Lösung>
```

Das Modell lernt dieses **Format** und kann es bei Inference wiedererkennen.

---

## 📖 Nächste Schritte

1. ✅ Dieses Tutorial durchlesen
2. ⬜ Baseline evaluieren (`./run_iteration.sh 0`)
3. ⬜ Baseline-Report analysieren
4. ⬜ Iteration 1 durchführen
5. ⬜ Vergleichs-Report studieren
6. ⬜ Jupyter Notebook öffnen für eigene Analysen
7. ⬜ Eigene Trainingsdaten für Iteration 3 erstellen
8. ⬜ Visualisierungen interpretieren

**Zeit-Investition:** ~4-6 Stunden für vollständiges Verständnis

**Lernziel erreicht, wenn du:**
- ✅ Metriken interpretieren kannst
- ✅ Fehlertypen klassifizieren kannst
- ✅ Trainingsdaten designen kannst
- ✅ Verstehst, warum iteratives Lernen funktioniert

---

**Viel Erfolg! 🚀**

Bei Fragen: Siehe `README.md` für Kontakt-Infos oder öffne ein Issue.
