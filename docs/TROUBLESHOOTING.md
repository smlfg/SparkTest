# Troubleshooting Guide

**GPU Training Platform** | Version 1.0

This guide helps you diagnose and fix common issues. Each problem includes symptoms, causes, solutions, and prevention tips.

---

## Table of Contents

1. [GPU Issues](#gpu-issues)
2. [Memory Errors](#memory-errors)
3. [Training Problems](#training-problems)
4. [Data Loading Issues](#data-loading-issues)
5. [Model Issues](#model-issues)
6. [Dashboard & UI Problems](#dashboard--ui-problems)
7. [Network & Connectivity](#network--connectivity)
8. [Performance Issues](#performance-issues)

---

## GPU Issues

### Problem 1: GPU Not Detected

#### Symptoms
- Dashboard shows "0 GPUs available"
- Training job fails with "No GPU found"
- `nvidia-smi` command not found or shows no devices
- Error: `CUDA initialization: CUDA driver version is insufficient`

#### Causes
- GPU drivers not installed or outdated
- CUDA toolkit version mismatch
- Docker container not started with GPU access
- GPU reserved by another process
- Hardware failure

#### Solutions

**Solution 1: Check GPU availability**
```bash
# In terminal or notebook
nvidia-smi

# Should show GPUs like:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.85.12    Driver Version: 525.85.12    CUDA Version: 12.1     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# |   0  NVIDIA A100-SXM...  On   | 00000000:00:04.0 Off |                    0 |
```

**Solution 2: Restart environment**
```bash
# For notebook users
# Kernel → Restart Kernel

# For SSH users
# Exit and reconnect
exit
ssh your-username@platform-hostname
```

**Solution 3: Contact administrator**
If GPU still not visible, this is likely a system configuration issue:
- Email: support@platform-url.com
- Include: `nvidia-smi` output and error messages
- Admin will check:
  - GPU hardware status
  - Driver installation
  - CUDA configuration
  - Resource allocation

#### Prevention
- Regular system maintenance (admin responsibility)
- Monitor GPU health in dashboard
- Report unusual behavior early
- Don't modify system CUDA/driver installations

---

### Problem 2: GPU Memory Leak

#### Symptoms
- GPU memory usage increases over time
- Eventually hits "CUDA out of memory"
- Doesn't happen immediately, but after many training steps
- Memory not released after job completion

#### Causes
- Python objects holding GPU tensors not garbage collected
- Gradients accumulating without clearing
- Cached values in model
- Memory fragmentation

#### Solutions

**Solution 1: Clear cache regularly**
```python
import torch

# Add to training loop (every few hundred steps)
if step % 100 == 0:
    torch.cuda.empty_cache()
```

**Solution 2: Explicitly delete tensors**
```python
# After using large tensors
del large_tensor
torch.cuda.empty_cache()
```

**Solution 3: Restart training job**
- Stop current job
- Clear all GPU memory
- Restart from last checkpoint

**Solution 4: Enable memory monitoring**
```yaml
# In training config
monitoring:
  track_gpu_memory: true
  memory_alert_threshold: 90  # Alert at 90% usage
```

#### Prevention
- Use context managers for temporary tensors
- Call `.detach()` when storing metrics
- Limit validation batch size
- Regular cache clearing in training loop
- Monitor memory trends in dashboard

---

## Memory Errors

### Problem 3: CUDA Out of Memory

#### Symptoms
```
RuntimeError: CUDA out of memory. Tried to allocate X GB (GPU 0; total capacity Y GB; already allocated Z GB)
```
- Training crashes shortly after starting
- Works with smaller batch size
- More likely with larger models

#### Causes
- Batch size too large for available GPU memory
- Model too large for GPU
- Sequence length too long
- Gradient accumulation consuming memory
- Other processes using GPU memory

#### Solutions

**Solution 1: Reduce batch size** (Immediate fix)
```yaml
# In training configuration
train_batch_size: 1  # Start minimal
gradient_accumulation_steps: 8  # Maintain effective batch size
```

**Solution 2: Enable memory optimization**
```yaml
# Enable all memory-saving features
gradient_checkpointing: true  # Trade compute for memory
use_lora: true                # Fine-tune small adapter
mixed_precision: "bf16"       # Use 16-bit instead of 32-bit
```

**Solution 3: Reduce sequence length**
```yaml
max_length: 512  # Instead of 2048
# Or use dynamic padding
padding: "longest"  # Don't pad to max unnecessarily
```

**Solution 4: Use smaller base model**
```yaml
# Instead of LLaMA-13B, try LLaMA-7B
# Instead of GPT-J-6B, try GPT-2-large (774M)
model_name: "gpt2-large"
```

**Solution 5: Distributed training**
```yaml
# Split across multiple GPUs
num_gpus: 4
# Or use FSDP for very large models
strategy: "fsdp"
```

**Memory calculation reference**:
```
Required Memory (GB) ≈
  Model Parameters (B) × 4 bytes (fp32) or 2 bytes (fp16) × 4 (optimizer states + gradients)
  + Batch Size × Sequence Length × Hidden Size × 2 bytes

Example: GPT-2 (1.5B params), batch=8, seq=1024, fp16
  = 1.5B × 2 × 4 + 8 × 1024 × 1600 × 2 / 1e9
  = 12 GB + 0.025 GB
  ≈ 12 GB
```

#### Prevention
- Start with small batch size, increase gradually
- Always enable gradient checkpointing for large models
- Use LoRA by default
- Monitor memory usage in dashboard
- Test configuration on small dataset first

---

### Problem 4: CPU Out of Memory

#### Symptoms
```
MemoryError: Unable to allocate X GB for an array
```
- Happens during data loading
- System becomes unresponsive
- Error before GPU training starts

#### Causes
- Loading entire dataset into RAM
- Inefficient data processing
- Too many data loader workers
- Large model checkpoint loading

#### Solutions

**Solution 1: Use streaming dataset**
```python
from datasets import load_dataset

# Don't load all to memory
dataset = load_dataset("json", data_files="data.jsonl", streaming=True)
```

**Solution 2: Reduce data loader workers**
```yaml
dataloader_num_workers: 2  # Instead of 8 or 16
```

**Solution 3: Process data in chunks**
```python
# Instead of
data = pd.read_csv("huge_file.csv")  # Loads all

# Use
for chunk in pd.read_csv("huge_file.csv", chunksize=10000):
    process(chunk)
```

**Solution 4: Use memory-mapped files**
```python
import numpy as np

# Memory-mapped array (stays on disk)
data = np.memmap("data.npy", dtype='float32', mode='r', shape=(1000000, 768))
```

#### Prevention
- Design datasets for streaming
- Avoid loading full dataset into memory
- Monitor RAM usage
- Use appropriate number of workers (typically 4-8)

---

## Training Problems

### Problem 5: Training Stuck at 0% or Not Starting

#### Symptoms
- Progress bar stuck at "Initializing..." or 0%
- No log output for >10 minutes
- GPU shows 0% utilization
- Job status shows "Running" but nothing happening

#### Causes
- Data loading bottleneck (processing first batch)
- Model initialization taking long time
- Network issues downloading pre-trained weights
- Deadlock in distributed training
- Incorrect configuration

#### Solutions

**Solution 1: Check logs**
```bash
# In dashboard: Training Job → View Logs
# Look for last message, often indicates where it's stuck
```

**Solution 2: Wait longer for large models**
- GPT-J (6B): Can take 5-10 minutes to initialize
- LLaMA-13B: Can take 10-20 minutes
- Check GPU memory usage increasing = likely loading

**Solution 3: Test data loading separately**
```python
# In notebook, test if data loads
from torch.utils.data import DataLoader
loader = DataLoader(dataset, batch_size=8)
batch = next(iter(loader))  # Should complete in seconds
print("Data loading works!")
```

**Solution 4: Restart with debugging**
```yaml
# Enable verbose logging
logging_level: "DEBUG"
log_first_batch: true
```

**Solution 5: Simplify configuration**
- Use default template
- Reduce to 1 GPU
- Use smallest base model
- Tiny dataset (100 examples)
- If this works, gradually add complexity

#### Prevention
- Start with simple configuration
- Test data loading first
- Monitor initialization logs
- Use pre-downloaded models when possible

---

### Problem 6: Training Loss is NaN or Infinity

#### Symptoms
```
Step 50: loss = nan
Step 51: loss = inf
```
- Loss becomes NaN (Not a Number) during training
- Or loss explodes to infinity
- Training can't recover

#### Causes
- Learning rate too high
- Numerical instability
- Gradient explosion
- Bad data (NaN values, inf values)
- Mixed precision overflow

#### Solutions

**Solution 1: Reduce learning rate**
```yaml
# If using 1e-4, try
learning_rate: 5e-5
# Or even
learning_rate: 1e-5
```

**Solution 2: Enable gradient clipping**
```yaml
max_grad_norm: 1.0  # Clip gradients above this value
```

**Solution 3: Check data for NaN**
```python
import numpy as np
import pandas as pd

# For CSV data
df = pd.read_csv("data.csv")
print("NaN values:", df.isna().sum())
print("Inf values:", np.isinf(df.select_dtypes(include=[np.number])).sum())

# Remove bad rows
df = df.dropna()
```

**Solution 4: Use more stable optimizer**
```yaml
optimizer:
  type: "AdamW"  # More stable than SGD
  eps: 1e-8      # Numerical stability
```

**Solution 5: Disable mixed precision temporarily**
```yaml
mixed_precision: "no"  # Or "fp32"
# Once stable, can re-enable
```

**Solution 6: Restart from earlier checkpoint**
- Load checkpoint before NaN occurred
- Reduce learning rate
- Continue training

#### Prevention
- Start with conservative learning rate (1e-5 to 5e-5)
- Always enable gradient clipping
- Validate data has no NaN/inf values
- Use warmup steps
- Monitor loss trends in real-time

---

### Problem 7: Validation Loss Increasing While Training Loss Decreases

#### Symptoms
- Training loss steadily decreases
- Validation loss increases or plateaus
- Gap between training and validation loss grows
- Model outputs look good on training data, poor on new data

#### Causes
- **Overfitting**: Model memorizing training data
- Training data not representative
- Model too large for dataset size
- Training too long

#### Solutions

**Solution 1: Early stopping** (Automatic)
```yaml
early_stopping:
  enabled: true
  patience: 3          # Stop if no improvement for 3 epochs
  monitor: "val_loss"
  mode: "min"
```

**Solution 2: Regularization**
```yaml
# Add regularization
weight_decay: 0.01      # L2 regularization
dropout: 0.1            # Dropout layers
```

**Solution 3: Get more data**
- Increase dataset size (most effective)
- Use data augmentation
- Combine multiple datasets

**Solution 4: Reduce model capacity**
```yaml
# Use smaller model
model_name: "gpt2-medium"  # Instead of gpt2-large

# Or reduce LoRA rank
lora_r: 16  # Instead of 64
```

**Solution 5: Use best checkpoint, not latest**
```python
# Don't use final checkpoint
model = load_model("checkpoint-best")  # Best validation loss
# Not load_model("checkpoint-latest")
```

#### Prevention
- Monitor validation loss from start
- Enable early stopping
- Use sufficient data (1000+ examples recommended)
- Start with smaller models
- Regularization by default

---

### Problem 8: Training Much Slower Than Expected

#### Symptoms
- ETA shows days instead of hours
- GPU utilization < 50%
- Steps per second very low (<0.1)
- Expected 2 hours, taking 20 hours

#### Causes
- Data loading bottleneck (CPU can't feed GPU fast enough)
- Small batch size (GPU underutilized)
- Inefficient data preprocessing
- Network latency (reading from remote storage)
- Excessive logging or checkpointing

#### Solutions

**Solution 1: Increase data loader workers**
```yaml
dataloader_num_workers: 8  # Parallel data loading
pin_memory: true           # Faster CPU→GPU transfer
```

**Solution 2: Increase batch size**
```yaml
# If memory allows
train_batch_size: 16  # Instead of 4
# Or use gradient accumulation
train_batch_size: 8
gradient_accumulation_steps: 4  # Effective batch size: 32
```

**Solution 3: Optimize data preprocessing**
```python
# Pre-process and save
processed_dataset = dataset.map(
    preprocess_function,
    batched=True,
    num_proc=8,  # Parallel processing
)
processed_dataset.save_to_disk("processed_data")

# Then load processed data
dataset = load_from_disk("processed_data")
```

**Solution 4: Reduce checkpoint frequency**
```yaml
save_steps: 1000  # Instead of 100
logging_steps: 50  # Instead of 10
```

**Solution 5: Use local storage**
- Copy dataset to local SSD
- Don't read from network drive during training

**Solution 6: Enable mixed precision**
```yaml
mixed_precision: "bf16"  # Faster on modern GPUs
```

#### Prevention
- Profile data loading (see GPU utilization)
- Pre-process data before training
- Use appropriate batch size
- Store data locally
- Monitor steps/second metric

---

## Data Loading Issues

### Problem 9: "Dataset Not Found" or Loading Errors

#### Symptoms
```
FileNotFoundError: [Errno 2] No such file or directory: '/workspace/data/my_dataset'
```
- Training fails at data loading stage
- Error mentions missing files or directories

#### Causes
- Wrong file path
- Dataset not uploaded successfully
- Permissions issue
- Typo in dataset name

#### Solutions

**Solution 1: Verify dataset path**
```bash
# In terminal or notebook
ls /workspace/data/

# Check specific dataset
ls -lh /workspace/data/my_dataset/
```

**Solution 2: Check dashboard**
- Navigate to Datasets
- Verify dataset shows "Ready" status
- Not "Processing" or "Failed"

**Solution 3: Re-upload dataset**
- Delete failed upload
- Upload again
- Wait for validation to complete

**Solution 4: Fix path in configuration**
```yaml
# Make sure path matches exactly
train_data: "/workspace/data/my_dataset/train.jsonl"
# Not "my_dataset/train.jsonl" (missing /workspace/data/)
```

**Solution 5: Check permissions**
```bash
# Should be readable
chmod 644 /workspace/data/my_dataset/train.jsonl
```

#### Prevention
- Use dashboard file browser to get exact paths
- Copy-paste paths instead of typing
- Verify upload completion before training
- Use standard locations (/workspace/data/)

---

### Problem 10: Data Loading Very Slow

#### Symptoms
- "Loading data..." takes >30 minutes
- First epoch takes much longer than subsequent epochs
- High CPU usage, low GPU usage

#### Causes
- Large dataset loading into memory
- Inefficient file format
- Reading from slow storage
- Heavy preprocessing

#### Solutions

**Solution 1: Use efficient format**
```bash
# Convert CSV to Parquet (much faster)
python -c "
import pandas as pd
df = pd.read_csv('data.csv')
df.to_parquet('data.parquet')
"
```

**Solution 2: Pre-tokenize data**
```python
# Tokenize once, save, reuse
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenized = dataset.map(
    lambda x: tokenizer(x["text"], truncation=True, padding="max_length"),
    batched=True,
    num_proc=8,
)
tokenized.save_to_disk("tokenized_data")

# In training, just load
dataset = load_from_disk("tokenized_data")
```

**Solution 3: Use streaming for huge datasets**
```python
dataset = load_dataset("json", data_files="huge.jsonl", streaming=True)
```

#### Prevention
- Use Parquet or Arrow format for large datasets
- Pre-tokenize when possible
- Test data loading before training
- Use streaming for datasets > 10GB

---

## Model Issues

### Problem 11: Model Not Importing or Loading

#### Symptoms
```
OSError: Model 'my-model' not found
ValueError: Unrecognized configuration class
```
- Can't load pre-trained model
- Model architecture errors

#### Causes
- Typo in model name
- Model not available in HuggingFace
- Network issues downloading
- Incompatible model format

#### Solutions

**Solution 1: Check model name**
```python
# Correct format
model = AutoModel.from_pretrained("gpt2")
# Not "GPT2" or "gpt-2"

# For HuggingFace models
model = AutoModel.from_pretrained("username/model-name")
```

**Solution 2: Browse available models**
- Dashboard → Models → Browse
- Or visit: huggingface.co/models
- Copy exact model identifier

**Solution 3: Pre-download model**
```bash
# Download manually first
huggingface-cli download gpt2

# Then use
model = AutoModel.from_pretrained("gpt2", local_files_only=True)
```

**Solution 4: Check model type**
```python
# For language modeling
from transformers import AutoModelForCausalLM

# For classification
from transformers import AutoModelForSequenceClassification

# For text-to-image
from diffusers import FluxPipeline
```

#### Prevention
- Use models from dashboard dropdown
- Test model loading in notebook first
- Check HuggingFace model card
- Keep model names in config files

---

### Problem 12: Model Outputs Are Always the Same

#### Symptoms
- Every input produces identical output
- No variation regardless of prompt
- Model seems to ignore input

#### Causes
- Temperature set to 0 (deterministic)
- Model not properly fine-tuned
- Stuck in local minimum
- Generation parameters too restrictive

#### Solutions

**Solution 1: Adjust temperature**
```python
output = model.generate(
    input_ids,
    temperature=0.8,  # Increase from 0 or very low value
    do_sample=True,   # Enable sampling
)
```

**Solution 2: Use nucleus sampling**
```python
output = model.generate(
    input_ids,
    top_p=0.9,        # Nucleus sampling
    top_k=50,         # Top-k sampling
    do_sample=True,
)
```

**Solution 3: Check model training**
- Verify training loss decreased
- Check validation metrics
- Test with base model to compare

**Solution 4: Increase max length**
```python
output = model.generate(
    input_ids,
    max_length=200,   # Allow longer outputs
    min_length=20,    # Force minimum length
)
```

#### Prevention
- Always use temperature > 0.5 for diverse outputs
- Enable sampling
- Verify training succeeded
- Test generation parameters in notebook

---

## Dashboard & UI Problems

### Problem 13: WebUI Not Loading

#### Symptoms
- Blank white page
- "Connection refused" error
- Page loads but no content
- Infinite loading spinner

#### Causes
- Service not running
- Wrong URL or port
- Network/firewall issues
- Browser cache issues
- VPN not connected

#### Solutions

**Solution 1: Check URL**
```
Correct: http://platform-hostname:8002
Not: https://... (unless SSL configured)
Not: http://localhost:8002 (unless on server)
```

**Solution 2: Verify service running**
```bash
# For admin/advanced users
curl http://localhost:8002/health
# Should return: {"status": "healthy"}
```

**Solution 3: Clear browser cache**
- Chrome: Ctrl+Shift+Delete → Clear cache
- Firefox: Ctrl+Shift+Delete → Cached content
- Or try incognito/private window

**Solution 4: Check VPN**
- Ensure VPN connected
- Try disconnecting and reconnecting
- Check VPN status in system tray

**Solution 5: Try different browser**
- Chrome instead of Firefox
- Edge instead of Safari
- Updated browser version

**Solution 6: Contact admin**
If none work:
- Email: support@platform-url.com
- Include: Error message, screenshot, browser version

#### Prevention
- Bookmark correct URL
- Keep VPN connected
- Use supported browsers
- Clear cache regularly

---

### Problem 14: Dashboard Shows Wrong Information

#### Symptoms
- GPU count incorrect
- Old jobs still showing as "Running"
- Metrics not updating
- Dataset shows "Processing" forever

#### Causes
- Cache issues
- Service synchronization lag
- Database inconsistency

#### Solutions

**Solution 1: Refresh page**
```
Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

**Solution 2: Clear browser cache**
```
Settings → Privacy → Clear browsing data → Cached images and files
```

**Solution 3: Wait for sync**
- Some operations take time
- Wait 5-10 minutes
- Check again

**Solution 4: Check job status in logs**
```bash
# Via SSH
tail -f /workspace/logs/job-12345.log
```

**Solution 5: Report to admin**
If persistent:
- Screenshot of issue
- Job ID or dataset name
- What you expect vs. what shows

#### Prevention
- Hard refresh regularly
- Don't rely on cached data
- Verify critical info in logs

---

## Network & Connectivity

### Problem 15: Can't Connect via SSH

#### Symptoms
```
ssh: connect to host platform-hostname port 22: Connection refused
Permission denied (publickey)
```

#### Causes
- SSH not enabled for account
- Wrong hostname or port
- SSH key not configured
- VPN not connected
- Firewall blocking

#### Solutions

**Solution 1: Check if SSH enabled**
- Dashboard → Settings → SSH Access
- If disabled, request from admin

**Solution 2: Verify hostname and port**
```bash
# Standard SSH
ssh username@platform-hostname

# Custom port
ssh -p 2222 username@platform-hostname
```

**Solution 3: Add SSH key**
```bash
# Generate key if don't have
ssh-keygen -t ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to platform: Dashboard → Settings → SSH Keys
```

**Solution 4: Connect VPN first**
```bash
# Connect to VPN
sudo openvpn config.ovpn

# Then SSH
ssh username@platform-hostname
```

**Solution 5: Use web terminal**
- Dashboard → Terminal (in-browser SSH)
- No SSH client needed

#### Prevention
- Set up SSH keys during onboarding
- Test connection before needed
- Keep VPN connected
- Save connection details

---

### Problem 16: Slow Upload/Download

#### Symptoms
- Dataset upload takes hours
- Model download very slow
- Notebook saves slow
- Network timeout errors

#### Causes
- Large files over slow network
- Many concurrent users
- Network congestion
- Server under load

#### Solutions

**Solution 1: Use compression**
```bash
# Compress before upload
tar -czf dataset.tar.gz dataset/
# Upload compressed file
# Platform auto-extracts
```

**Solution 2: Resume capability**
```bash
# Use rsync (can resume)
rsync -avz --progress data/ username@host:/workspace/data/

# Or scp with resume
# Not possible with scp, use rsync
```

**Solution 3: Upload during off-peak**
- Evenings/weekends may be slower
- Try early morning
- Check status page for maintenance

**Solution 4: Split large files**
```bash
# Split into 1GB chunks
split -b 1G large_file.zip part_

# Upload separately
# Recombine on server
cat part_* > large_file.zip
```

**Solution 5: Use cloud import**
- Upload to S3/GCS first (faster)
- Import from cloud to platform
- Platform has better bandwidth

#### Prevention
- Compress large datasets
- Upload during off-peak hours
- Use cloud import for >10GB
- Plan uploads in advance

---

## Performance Issues

### Problem 17: Low GPU Utilization

#### Symptoms
- `nvidia-smi` shows GPU at 20-50% utilization
- Training slower than expected
- GPU memory used but computation low

#### Causes
- Data loading bottleneck
- Batch size too small
- CPU preprocessing limiting GPU
- Inefficient model

#### Solutions

**Solution 1: Increase data loading**
```yaml
dataloader_num_workers: 8  # More parallel workers
prefetch_factor: 4         # Pre-load batches
pin_memory: true          # Faster transfer
```

**Solution 2: Increase batch size**
```yaml
# If memory allows
train_batch_size: 16  # Was: 4
# Monitor GPU memory usage
```

**Solution 3: Reduce preprocessing**
```python
# Pre-process once, save
dataset.save_to_disk("processed")
# Load processed version
dataset = load_from_disk("processed")
```

**Solution 4: Profile bottleneck**
```python
import torch.profiler

with torch.profiler.profile() as prof:
    model(batch)
print(prof.key_averages().table())
# Identifies slow operations
```

#### Prevention
- Aim for >80% GPU utilization
- Balance batch size and memory
- Pre-process data
- Monitor utilization dashboard

---

### Problem 18: Inference Very Slow

#### Symptoms
- Each prediction takes >10 seconds
- Batch inference slower than expected
- Interactive notebook laggy

#### Causes
- Model too large
- Running on CPU instead of GPU
- No optimization applied
- Memory swapping

#### Solutions

**Solution 1: Ensure GPU usage**
```python
import torch

# Check
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Model device: {next(model.parameters()).device}")

# Move to GPU if needed
model = model.to("cuda")
```

**Solution 2: Quantization**
```python
# Load in 8-bit (4x smaller, 2x faster)
model = AutoModelForCausalLM.from_pretrained(
    "model-name",
    load_in_8bit=True,
    device_map="auto"
)
```

**Solution 3: Reduce max length**
```python
output = model.generate(
    input_ids,
    max_length=100,  # Instead of 512
)
```

**Solution 4: Use batching**
```python
# Instead of one-by-one
outputs = model.generate(
    batch_input_ids,  # Batch of inputs
    batch_size=8,
)
```

**Solution 5: Export to ONNX**
```python
# Convert for faster inference
torch.onnx.export(model, ...)
# Use with ONNX Runtime (much faster)
```

#### Prevention
- Test inference speed before deploying
- Use quantization for production
- Batch requests when possible
- Monitor inference metrics

---

## Advanced Debugging

### Getting Detailed Logs

**Enable debug logging**:
```yaml
logging:
  level: "DEBUG"
  save_to_file: true
  file_path: "/workspace/logs/debug.log"
```

**View live logs**:
```bash
# Dashboard: Job → View Logs → Live mode

# Or SSH
tail -f /workspace/logs/training-job-ID.log
```

**Download logs**:
- Dashboard → Job → Download Logs
- Includes: training, error, system logs

### System Diagnostics

**Check system health**:
```bash
# GPU status
nvidia-smi

# Disk space
df -h /workspace

# Memory
free -h

# CPU
top

# Network
ping platform-hostname
```

**Platform health check**:
- Dashboard → System Status
- Shows: GPU, storage, network, services

### Reporting Bugs

**Good bug report includes**:
1. **What you were trying to do**
2. **What happened instead**
3. **Error messages** (exact text)
4. **Steps to reproduce**
5. **Environment**:
   - Model name
   - Dataset size
   - Configuration
   - Browser (for UI issues)
6. **Logs** (attached)
7. **Screenshots** (if UI issue)

**Example**:
```
Subject: Training fails with "NaN loss" on GPT-2 fine-tuning

Description:
I'm trying to fine-tune GPT-2 on a customer support dataset.
Training runs for ~100 steps then crashes with NaN loss.

Steps to reproduce:
1. Upload dataset "customer-support-chat.csv" (500 examples)
2. Select GPT-2 base model
3. Use default chatbot template
4. Click "Start Training"
5. After ~100 steps: loss becomes NaN

Configuration:
- Model: gpt2 (124M)
- Dataset: 500 examples, CSV format
- Template: Chatbot (default settings)
- GPUs: 1x A100

Error logs: (attached training-job-12345.log)
Line 245: "RuntimeError: Loss is NaN at step 103"

Expected: Training should complete successfully
Actual: Crashes with NaN loss

Screenshot: (attached dashboard-error.png)
```

---

## Getting Help

**Self-Service**:
1. Search this guide
2. Check [FAQ](FAQ.md)
3. Read [Student Handbook](STUDENT_HANDBOOK.md)

**Community**:
- Forum: forum.platform-url.com
- Slack: #gpu-training-help
- Office hours: Wed 2-3 PM

**Direct Support**:
- Email: support@platform-url.com
- Response time: 24 hours
- Include: Job ID, logs, error messages

**Emergency** (system down):
- Phone: +49-XXX-XXXX
- Email: urgent@platform-url.com

---

## Preventive Maintenance

### Best Practices

✅ **Before training**:
- Validate dataset
- Test on small subset
- Check resource availability
- Save configuration

✅ **During training**:
- Monitor metrics
- Check logs periodically
- Watch GPU utilization
- Save checkpoints frequently

✅ **After training**:
- Validate outputs
- Save final model
- Document configuration
- Clean up old checkpoints

### Regular Checks

**Daily**:
- Check training progress
- Review error logs
- Monitor resource usage

**Weekly**:
- Clean up old datasets
- Delete unused checkpoints
- Review performance trends

**Monthly**:
- Update configurations
- Optimize workflows
- Request quota adjustments

---

*Last updated: January 12, 2025*

**Didn't find your issue? Email: support@platform-url.com**
