# Use Case: Text Classification

**Complete guide to fine-tuning classification models**

---

## Overview

This guide covers fine-tuning models for text classification tasks including sentiment analysis, topic categorization, spam detection, intent classification, and more.

**What you'll learn**:
- Preparing classification datasets
- Handling imbalanced classes
- Recommended configurations
- Evaluation metrics
- Production deployment

**Time required**: 1-3 hours (training) + 30 minutes (setup)

---

## Use Cases

### 1. Sentiment Analysis
- Product reviews (positive/negative/neutral)
- Customer feedback classification
- Social media monitoring
- Brand sentiment tracking

### 2. Topic Categorization
- News article classification
- Support ticket routing
- Content tagging
- Document organization

### 3. Intent Classification
- Chatbot intent detection
- Voice assistant command classification
- Email routing
- Query understanding

### 4. Spam Detection
- Email spam filtering
- Comment moderation
- Fraud detection
- Abuse detection

### 5. Language Detection
- Identify language of text
- Multilingual content routing
- Translation pre-processing

---

## Dataset Format

### Binary Classification (2 classes)

**CSV format** (simplest):
```csv
text,label
"This product is amazing!",positive
"Terrible experience, would not recommend",negative
"Decent quality for the price",positive
"Complete waste of money",negative
```

**JSONL format**:
```json
{"text": "This product is amazing!", "label": "positive"}
{"text": "Terrible experience, would not recommend", "label": "negative"}
```

### Multi-Class Classification (3+ classes)

**CSV**:
```csv
text,category
"Stock market hits new high",business
"Local team wins championship",sports
"New vaccine approved by FDA",health
"Breakthrough in quantum computing",technology
```

**JSONL**:
```json
{"text": "Stock market hits new high", "label": "business"}
{"text": "Local team wins championship", "label": "sports"}
{"text": "New vaccine approved by FDA", "label": "health"}
```

### Multi-Label Classification (multiple labels per example)

**JSONL** (required for multi-label):
```json
{"text": "Electric car company opens new factory", "labels": ["business", "technology", "automotive"]}
{"text": "Olympic athlete wins gold medal", "labels": ["sports", "news"]}
{"text": "Study shows coffee health benefits", "labels": ["health", "science"]}
```

### Dataset Structure

```
classification-data/
├── train.csv           # 80% of data (minimum 500 examples)
├── validation.csv      # 10% of data (minimum 50 examples)
└── test.csv            # 10% of data (minimum 50 examples)
```

---

## Data Collection & Preparation

### Data Sources

**1. Labeled Data**:
- Existing labeled datasets (Kaggle, HuggingFace)
- Historical data with labels
- Customer feedback with ratings
- Previously categorized content

**2. Human Labeling**:
```python
# Create labeling interface
import pandas as pd

unlabeled = pd.read_csv("unlabeled_data.csv")

# Manual labeling or use tools like:
# - Label Studio
# - Prodigy
# - Amazon Mechanical Turk

labeled = []
for text in unlabeled['text']:
    label = input(f"'{text[:100]}...' - Label: ")
    labeled.append({"text": text, "label": label})

pd.DataFrame(labeled).to_csv("labeled_data.csv", index=False)
```

**3. Weak Supervision**:
```python
# Use rules for initial labels, then manually review
def weak_label(text):
    text_lower = text.lower()
    if "love" in text_lower or "great" in text_lower:
        return "positive"
    elif "hate" in text_lower or "terrible" in text_lower:
        return "negative"
    else:
        return "neutral"

# Apply and review
df['predicted_label'] = df['text'].apply(weak_label)
# Manually review and correct
```

### Class Distribution

**Balanced** (ideal):
```
positive: 1000 examples (33%)
negative: 1000 examples (33%)
neutral:  1000 examples (33%)
```

**Imbalanced** (common):
```
positive: 2000 examples (80%)
negative:  300 examples (12%)
neutral:   200 examples (8%)
```

**Handling imbalanced data**:

**Option 1: Oversampling minority class**:
```python
from imblearn.over_sampling import RandomOverSampler

ros = RandomOverSampler(random_state=42)
X_resampled, y_resampled = ros.fit_resample(X, y)
```

**Option 2: Undersampling majority class**:
```python
from imblearn.under_sampling import RandomUnderSampler

rus = RandomUnderSampler(random_state=42)
X_resampled, y_resampled = rus.fit_resample(X, y)
```

**Option 3: Class weights** (recommended):
```yaml
# In training config
class_weights: "balanced"
# Or specify manually
class_weights: {0: 1.0, 1: 2.0, 2: 3.0}
```

### Data Quality Checklist

✅ **Clear labels**: Each class well-defined
✅ **Consistent labeling**: Same criteria across dataset
✅ **Sufficient examples**: Minimum 50 per class, ideal 500+
✅ **Balanced or weighted**: Handle class imbalance
✅ **Representative**: Covers real-world distribution
✅ **Clean text**: Remove/handle special characters
✅ **No leakage**: Test data completely separate
✅ **Validated**: Sample reviewed for accuracy

### Minimum Data Requirements

| Task Complexity | Classes | Min per Class | Recommended |
|-----------------|---------|---------------|-------------|
| Simple Binary | 2 | 100 | 1,000 |
| Binary | 2 | 500 | 2,000 |
| Multi-class (3-10) | 3-10 | 100 | 500 |
| Multi-class (10+) | 10+ | 50 | 200 |
| Multi-label | Varies | 200 total | 1,000+ |

---

## Recommended Configuration

### Model Selection

**For simple classification** (2-5 classes, clear differences):
```yaml
model_name: "distilbert-base-uncased"
# Fast, efficient, good performance
# Memory: ~2GB
# Training time: 30 min - 1 hour
```

**For standard classification** (recommended):
```yaml
model_name: "bert-base-uncased"
# Excellent performance on most tasks
# Memory: ~4GB
# Training time: 1-2 hours
```

**For advanced/domain-specific**:
```yaml
model_name: "roberta-large"
# or "microsoft/deberta-v3-large"
# Best accuracy, slower
# Memory: ~8GB
# Training time: 3-5 hours
```

**For multilingual**:
```yaml
model_name: "bert-base-multilingual-cased"
# or "xlm-roberta-base"
# Supports 100+ languages
```

### Training Configuration

**Binary classification example**:

```yaml
# Task
task: "classification"
num_labels: 2  # or 3, 4, etc.
label_names: ["negative", "positive"]  # Optional

# Model
model_name: "bert-base-uncased"
use_lora: true  # Recommended for efficiency
lora_config:
  r: 16  # Lower than generation tasks
  alpha: 16
  dropout: 0.1
  target_modules: ["query", "value"]

# Training
num_epochs: 3
learning_rate: 2e-5  # Standard for BERT-based models
lr_scheduler: "linear"
warmup_ratio: 0.1

# Batch size
per_device_train_batch_size: 16
per_device_eval_batch_size: 32
gradient_accumulation_steps: 2

# Optimization
mixed_precision: "fp16"
max_length: 128  # Shorter for classification
weight_decay: 0.01

# Class imbalance handling
class_weights: "balanced"  # Or specify per class

# Evaluation
eval_strategy: "epoch"
save_strategy: "epoch"
load_best_model_at_end: true
metric_for_best_model: "f1"  # or "accuracy", "precision", "recall"

# Early stopping
early_stopping_patience: 3
```

**Multi-class configuration**:
```yaml
# Main differences
num_labels: 5  # Number of classes
label_names: ["class1", "class2", "class3", "class4", "class5"]
metric_for_best_model: "f1_macro"  # Macro-averaged F1
```

**Multi-label configuration**:
```yaml
# Main differences
problem_type: "multi_label_classification"
num_labels: 10  # Number of possible labels
# Each example can have multiple labels
```

---

## Training Process

### Step 1: Prepare Dataset

**Convert to platform format**:
```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load your data
df = pd.read_csv("raw_data.csv")

# Split
train_df, temp_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42, stratify=temp_df['label'])

# Save
train_df.to_csv("train.csv", index=False)
val_df.to_csv("validation.csv", index=False)
test_df.to_csv("test.csv", index=False)

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
print(f"Class distribution:\n{train_df['label'].value_counts()}")
```

### Step 2: Upload to Platform

1. Navigate to **Datasets** → **Upload New**
2. Select `train.csv`
3. Metadata:
   - Name: `sentiment-classification-v1`
   - Type: `Classification`
   - Classes: `positive, negative, neutral`
4. Upload validation and test sets
5. Verify class distribution in validation report

### Step 3: Configure Training

1. **Training** → **New Job**
2. Template: **Text Classification**
3. Select dataset
4. Base model: `bert-base-uncased`
5. Configure:
   ```yaml
   num_labels: 3  # Your number of classes
   max_length: 128
   learning_rate: 2e-5
   num_epochs: 3
   ```
6. Name job: `sentiment-classifier-v1`

### Step 4: Monitor

**Key metrics to watch**:
- **Training Loss**: Should decrease
- **Validation Loss**: Should decrease without overfitting
- **Accuracy**: Should increase (target: >85% for binary, >75% for multi-class)
- **F1 Score**: Balanced metric (target: >0.80)

**Expected timeline** (BERT-base, 1000 examples):
- DistilBERT: 30 minutes
- BERT-base: 1 hour
- RoBERTa-large: 3 hours

---

## Evaluation Metrics

### Accuracy

**Definition**: Percentage of correct predictions

```python
accuracy = correct_predictions / total_predictions

# Example: 85 correct out of 100 = 0.85 or 85%
```

**When to use**: Balanced datasets

**Target**:
- Binary: >90% (excellent), >85% (good), >80% (acceptable)
- Multi-class (5 classes): >80% (excellent), >70% (good)

### Precision, Recall, F1

**Precision**: Of predicted positives, how many are actually positive?
```
Precision = True Positives / (True Positives + False Positives)
```

**Recall**: Of actual positives, how many did we find?
```
Recall = True Positives / (True Positives + False Negatives)
```

**F1 Score**: Harmonic mean of precision and recall
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Example**:
```
True Positives: 80
False Positives: 10  (predicted positive, actually negative)
False Negatives: 20  (predicted negative, actually positive)

Precision = 80 / (80 + 10) = 0.89
Recall = 80 / (80 + 20) = 0.80
F1 = 2 * (0.89 * 0.80) / (0.89 + 0.80) = 0.84
```

### Confusion Matrix

Visualize classification errors:

```
                Predicted
              Neg   Pos   Neu
Actual  Neg   90    5     5
        Pos   10    85    5
        Neu   15    10    75

```

**Interpretation**:
- Diagonal (90, 85, 75): Correct predictions
- Off-diagonal: Errors
- Example: 10 negative examples classified as positive

**Generate in platform**:
```python
# In notebook after training
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Get predictions
predictions = model.predict(test_dataset)
y_pred = predictions.argmax(-1)
y_true = test_dataset['label']

# Plot
cm = confusion_matrix(y_true, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["negative", "positive", "neutral"])
disp.plot()
plt.savefig("confusion_matrix.png")
```

### Class-Specific Metrics

**Per-class F1 scores**:
```python
from sklearn.metrics import classification_report

print(classification_report(y_true, y_pred, target_names=["negative", "positive", "neutral"]))

# Output:
#               precision    recall  f1-score   support
#
#     negative       0.85      0.90      0.87       100
#     positive       0.88      0.85      0.86       100
#      neutral       0.82      0.75      0.78       100
#
#     accuracy                           0.83       300
#    macro avg       0.85      0.83      0.84       300
# weighted avg       0.85      0.83      0.84       300
```

**What to look for**:
- All classes should have F1 > 0.70
- Large differences indicate class imbalance or difficulty
- Low recall on a class: model misses examples (false negatives)
- Low precision on a class: model over-predicts (false positives)

---

## Common Pitfalls & Solutions

### Problem 1: Low Accuracy on Minority Class

**Symptom**: Model predicts majority class for everything

**Example**:
```
Classes: positive (2000), negative (200)
Model predicts "positive" for 95% of examples
Accuracy: 90% (but useless on negative class)
```

**Solution**:
```yaml
# Use class weights
class_weights: "balanced"

# Or oversample minority class
data_augmentation: true

# Or undersample majority class
# Focus on F1 score, not accuracy
metric_for_best_model: "f1_macro"
```

### Problem 2: Overfitting

**Symptom**:
- Training accuracy: 99%
- Validation accuracy: 70%

**Solution**:
```yaml
# More regularization
weight_decay: 0.1
dropout: 0.2

# More data (best solution)
# Or data augmentation

# Early stopping
early_stopping_patience: 2

# Smaller model
model_name: "distilbert-base-uncased"
```

### Problem 3: Confusing Similar Classes

**Symptom**: Model confuses "neutral" and "positive"

**Solution**:
```python
# Option 1: Merge confusing classes
# Combine "neutral" → "positive"

# Option 2: More training examples for confused classes

# Option 3: Better feature engineering
# Add domain-specific features
```

### Problem 4: Poor Performance on Short Text

**Symptom**: Works well on long reviews, fails on short tweets

**Solution**:
```yaml
# Use model trained on short text
model_name: "vinai/bertweet-base"  # For tweets

# Or include short examples in training
# Balance long and short in dataset
```

---

## Deployment Checklist

✅ **Test accuracy**: Meets target threshold
✅ **Per-class F1**: All classes >0.70
✅ **Confusion matrix**: No systematic errors
✅ **Edge cases**: Tested unusual inputs
✅ **Speed**: <100ms per prediction
✅ **Robustness**: Handles typos, slang, emojis
✅ **Calibration**: Confidence scores meaningful
✅ **Documentation**: Clear on limitations

---

## Advanced Tips

### Data Augmentation

Increase training data artificially:

```python
# Synonym replacement
"The movie was great" → "The film was excellent"

# Back-translation
English → German → English

# Paraphrasing
"I loved this product" → "This product was amazing"
```

**Implementation**:
```python
from nlpaug.augmenter.word import SynonymAug

aug = SynonymAug(aug_src='wordnet')

original = "The customer service was excellent"
augmented = aug.augment(original, n=3)
print(augmented)
# ["The client service was excellent",
#  "The customer help was excellent",
#  "The customer service was outstanding"]
```

### Ensemble Methods

Combine multiple models:

```python
# Train 3 models with different seeds
model1 = train(seed=42)
model2 = train(seed=123)
model3 = train(seed=456)

# Average predictions
predictions = (model1.predict(x) + model2.predict(x) + model3.predict(x)) / 3

# Or voting
final_prediction = majority_vote([model1.predict(x), model2.predict(x), model3.predict(x)])
```

**Improvement**: Typically 2-5% better accuracy

### Active Learning

Iteratively improve with strategic labeling:

```python
# 1. Train initial model
model = train(labeled_data)

# 2. Predict on unlabeled data
predictions = model.predict(unlabeled_data)

# 3. Find uncertain examples (low confidence)
uncertain = [x for x, conf in zip(unlabeled_data, predictions) if max(conf) < 0.7]

# 4. Label uncertain examples manually
newly_labeled = human_label(uncertain)

# 5. Add to training set and retrain
labeled_data += newly_labeled
model = train(labeled_data)
```

---

## Example Datasets

**Download sample datasets**:
- [Sentiment Analysis (IMDB reviews)](../examples/datasets/imdb-sentiment.csv)
- [Topic Classification (News articles)](../examples/datasets/news-topics.csv)
- [Intent Classification (Chatbot)](../examples/datasets/intent-classification.jsonl)
- [Spam Detection (Emails)](../examples/datasets/spam-detection.csv)

**External datasets**:
- HuggingFace: `datasets.load_dataset("emotion")`
- Kaggle: Various classification competitions
- UCI ML Repository: Many labeled datasets

---

## Configuration Templates

**Binary sentiment**:
```yaml
task: "classification"
model_name: "bert-base-uncased"
num_labels: 2
num_epochs: 3
learning_rate: 2e-5
metric_for_best_model: "f1"
```

**Multi-class topics**:
```yaml
task: "classification"
model_name: "roberta-base"
num_labels: 10
num_epochs: 5
learning_rate: 1e-5
metric_for_best_model: "f1_macro"
class_weights: "balanced"
```

**Multi-label tagging**:
```yaml
task: "classification"
problem_type: "multi_label_classification"
model_name: "bert-base-uncased"
num_labels: 15
learning_rate: 3e-5
threshold: 0.5  # For multi-label predictions
```

---

## Resources

**Documentation**:
- [Student Handbook](../STUDENT_HANDBOOK.md)
- [Evaluation Metrics Guide](../advanced/metrics.md)
- [Data Preparation Best Practices](../advanced/data-prep.md)

**Tools**:
- [Label Studio](https://labelstud.io/) - Data labeling
- [scikit-learn](https://scikit-learn.org/) - Metrics and preprocessing
- [imbalanced-learn](https://imbalanced-learn.org/) - Handling imbalanced data

**Support**:
- Forum: forum.platform-url.com/c/classification
- Slack: #text-classification
- Email: support@platform-url.com

---

*Last updated: January 12, 2025*
