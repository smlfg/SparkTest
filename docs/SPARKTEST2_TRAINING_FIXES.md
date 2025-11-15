# SparkTest2 Training Issues & Fixes

**Known deployment issues and solutions for SparkTest2 training**

---

## Issue 1: TRL 0.24.0 API Breaking Changes

### Problem
```python
TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'tokenizer'
TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_text_field'
```

### Root Cause
TRL 0.24.0 introduced breaking API changes:
- `tokenizer=` → `processing_class=`
- `dataset_text_field=` removed
- `packing=` removed
- `max_seq_length` handling changed

### Solution

**train.py fixes**:

```python
# OLD (trl < 0.24)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=formatted_dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    args=training_args,
    packing=False,
)

# NEW (trl >= 0.24)
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,  # Changed
    train_dataset=formatted_dataset,
    # dataset_text_field removed - uses dataset columns directly
    # max_seq_length handled via tokenizer.model_max_length
    args=training_args,
    # packing removed - handled automatically
)
```

**TrainingArguments fixes**:

```python
training_args = TrainingArguments(
    output_dir=args.output,
    num_train_epochs=args.epochs,
    per_device_train_batch_size=args.batch_size,
    gradient_accumulation_steps=args.gradient_accumulation_steps,
    warmup_ratio=args.warmup_ratio,

    # Optimizer
    learning_rate=args.learning_rate,
    optim="adamw_8bit",
    weight_decay=0.01,

    # Mixed precision
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    gradient_checkpointing=True,

    # IMPORTANT: Disable multiprocessing for Python 3.13 compatibility
    dataloader_num_workers=0,  # Fixes pickle errors

    # Misc
    seed=42,
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
)
```

---

## Issue 2: Python 3.13 Pickle/Multiprocessing Errors

### Problem
```python
File ".../dill/_dill.py", line 1847, in save_function
    obj2, name = _locate_function(obj, pickler)
TypeError: cannot pickle 'managedbuffer' object
```

### Root Cause
Python 3.13 has stricter pickle requirements. The `dataloader_num_workers > 0` causes multiprocessing pickle errors with complex objects.

### Solution

**Option 1: Disable multiprocessing** (quick fix):
```python
dataloader_num_workers=0  # Add to TrainingArguments
```

**Option 2: Use Python 3.11** (recommended):
```bash
# Remove Python 3.13 venv
cd ~/finetune/SparkTest2
rm -rf venv

# Create Python 3.11 venv
python3.11 -m venv venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Option 3: Use Conda** (most stable):
```bash
conda create -n sparktest python=3.11
conda activate sparktest
pip install -r requirements.txt
```

---

## Issue 3: Unsloth/Torch Version Compatibility

### Problem
```
Skipping import of cpp extensions due to incompatible torch version 2.9.1+cu128 for torchao version 0.14.1
```

### Root Cause
Unsloth requires specific torch/torchao versions. Warning is usually non-fatal but can cause slowdowns.

### Solution

**Check versions**:
```bash
python -c "import torch; print('Torch:', torch.__version__)"
python -c "import unsloth; print('Unsloth OK')"
```

**If issues persist**:
```bash
# Reinstall compatible versions
pip install --upgrade torch==2.5.0
pip install --upgrade torchao==0.14.0
pip install --force-reinstall "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
```

---

## Complete Fix Script

Save as `fix_training.sh`:

```bash
#!/bin/bash
set -e

echo "=== SparkTest2 Training Fix Script ==="

# 1. Check Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
echo "Current Python: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "⚠️  Python 3.13 detected - multiprocessing issues expected"
    echo "Recommendation: Use Python 3.11"

    if command -v python3.11 &> /dev/null; then
        echo "✓ Python 3.11 available"
        echo "Run: python3.11 -m venv venv"
    else
        echo "✗ Python 3.11 not found"
        echo "Install: sudo apt install python3.11 python3.11-venv"
    fi
fi

# 2. Apply train.py fixes
echo ""
echo "Step 2: Applying train.py fixes..."

# Backup original
cp train.py train.py.backup.$(date +%Y%m%d_%H%M%S)

# Apply fixes
sed -i 's/tokenizer=tokenizer/processing_class=tokenizer/g' train.py
sed -i '/dataset_text_field=/d' train.py
sed -i '/max_seq_length=MAX_SEQ_LENGTH/d' train.py
sed -i '/packing=False/d' train.py

# Add dataloader_num_workers=0 if not present
if ! grep -q "dataloader_num_workers" train.py; then
    sed -i '/gradient_checkpointing=True,/a\        dataloader_num_workers=0,  # Python 3.13 compatibility' train.py
fi

echo "✓ train.py patched"

# 3. Check dependencies
echo ""
echo "Step 3: Checking dependencies..."
source venv/bin/activate

if ! python -c "import trl" 2>/dev/null; then
    echo "✗ TRL not installed"
    echo "Run: pip install trl transformers datasets peft accelerate bitsandbytes"
    exit 1
fi

TRL_VERSION=$(python -c "import trl; print(trl.__version__)")
echo "TRL version: $TRL_VERSION"

if [[ "$TRL_VERSION" < "0.24" ]]; then
    echo "⚠️  Old TRL version detected (need >= 0.24.0)"
    echo "Run: pip install --upgrade trl"
fi

echo ""
echo "=== Fix Complete ==="
echo ""
echo "Next steps:"
echo "1. If using Python 3.13, switch to 3.11:"
echo "   rm -rf venv && python3.11 -m venv venv && source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "2. Start training:"
echo "   nohup python train.py --dataset datasets/example-chatbot.json --output experiments/overnight-001 --epochs 10 > training.log 2>&1 &"
echo ""
echo "3. Monitor:"
echo "   tail -f training.log"
```

---

## Quick Start (After Fixes)

```bash
# 1. Navigate to project
cd ~/finetune/SparkTest2

# 2. Switch to Python 3.11 (if using 3.13)
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install torch transformers datasets trl peft accelerate bitsandbytes
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# 4. Apply fixes (manual or use script above)
# Edit train.py:
# - Change tokenizer= to processing_class=
# - Remove dataset_text_field=
# - Remove max_seq_length= from SFTTrainer
# - Remove packing=
# - Add dataloader_num_workers=0 to TrainingArguments

# 5. Start training
nohup python train.py \
    --dataset datasets/example-chatbot.json \
    --output experiments/overnight-001 \
    --epochs 10 \
    > training_overnight.log 2>&1 &

# 6. Monitor
tail -f training_overnight.log

# 7. Check process
ps aux | grep train.py | grep -v grep
```

---

## Verification Checklist

Before starting overnight training:

- [ ] Python version is 3.11 (not 3.13)
- [ ] venv created with correct Python
- [ ] All dependencies installed: `pip list | grep -E "(torch|trl|unsloth|transformers)"`
- [ ] train.py patched for trl 0.24+ API
- [ ] `dataloader_num_workers=0` in TrainingArguments
- [ ] Dataset exists: `ls -lh datasets/example-chatbot.json`
- [ ] Output directory writable: `mkdir -p experiments/overnight-001`
- [ ] Test run: `python train.py --help` (no errors)

---

## Expected Training Timeline

**example-chatbot.json (20 examples, 10 epochs)**:

- Setup: 2-3 minutes (model loading)
- Training: ~5-10 minutes per epoch
- Total: ~1 hour for 10 epochs
- Output: experiments/overnight-001/lora/

**Monitoring**:
```bash
# Watch live
watch -n 5 'tail -20 training_overnight.log'

# Check GPU usage
nvidia-smi -l 5

# Check progress
ls -lh experiments/overnight-001/
```

---

## Troubleshooting

### Training stops immediately
```bash
# Check for errors
cat training_overnight.log

# Common issues:
# - Dataset not found: ls -lh datasets/
# - Permission denied: chmod +x train.py
# - Import errors: pip list | grep unsloth
```

### CUDA out of memory
```python
# Reduce batch size in train.py or command line:
python train.py --batch-size 1 --gradient-accumulation-steps 8
```

### Model not saving
```bash
# Check output directory
ls -lh experiments/overnight-001/

# Check disk space
df -h
```

---

## Contact

If issues persist:
- Check logs: `training_overnight.log`
- GitHub Issues: Link to SparkTest2 repo
- Agent 6 Documentation: For general training issues

---

*Last updated: November 15, 2024*
*Tested with: Python 3.11, TRL 0.24.0, Unsloth latest*
