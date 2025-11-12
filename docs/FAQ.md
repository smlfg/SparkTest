# Frequently Asked Questions (FAQ)

**GPU Training Platform** | Version 1.0

Quick answers to common questions. Can't find what you need? Check the [Student Handbook](STUDENT_HANDBOOK.md) or [Troubleshooting Guide](TROUBLESHOOTING.md).

---

## Table of Contents

- [Access & Login](#access--login)
- [Dataset Preparation](#dataset-preparation)
- [Training Issues](#training-issues)
- [Model Testing](#model-testing)
- [Performance](#performance)
- [Billing & Resources](#billing--resources)
- [Security & Privacy](#security--privacy)

---

## Access & Login

### Q1: How do I get access to the platform?

**A:** Contact your course instructor or platform administrator. They will:
1. Create your account
2. Send credentials to your email
3. Provide VPN configuration (if required)
4. Grant appropriate resource limits

### Q2: I forgot my password. What should I do?

**A:** Two options:
1. **Self-service**: Click "Forgot Password" on login page → Enter email → Check inbox for reset link
2. **Admin help**: Email support@platform-url.com with your username

### Q3: Can I access the platform from home?

**A:** Yes, if:
- VPN is configured (required for most installations)
- You're on an allowed network
- Your account has remote access enabled

Check Settings → Network Access to verify your permissions.

### Q4: Why can't I log in via SSH?

**A:** Common causes:
- SSH access not enabled (default for students)
- Wrong hostname or port
- VPN not connected
- SSH keys not configured

**Solution**: Use the web dashboard for most tasks. For SSH access, request it from your administrator and add your public key in Settings → SSH Keys.

### Q5: What browsers are supported?

**A:**
- ✅ **Recommended**: Chrome 100+, Firefox 100+, Edge 100+
- ⚠️ **Limited support**: Safari 15+ (some features may not work)
- ❌ **Not supported**: Internet Explorer, old browser versions

---

## Dataset Preparation

### Q6: What's the minimum dataset size for fine-tuning?

**A:** It depends on the task:
- **Chatbot/Dialogue**: Minimum 100 conversations, ideal 1,000+
- **Classification**: Minimum 50 examples per class, ideal 500+
- **Code Generation**: Minimum 500 examples, ideal 5,000+
- **Image Training**: Minimum 5 images, ideal 20-50

**Rule of thumb**: More data = better results, but quality > quantity.

### Q7: What file formats are accepted?

**A:**

**Text data**:
- `.jsonl` (recommended for most tasks)
- `.json` (array of objects)
- `.csv` (tabular data)
- `.txt` (plain text, one example per line)

**Images**:
- `.jpg`, `.jpeg`, `.png`
- Resolution: 512x512 to 2048x2048

**Archives**:
- `.zip`, `.tar.gz` (automatically extracted)

### Q8: Can I use datasets in languages other than English?

**A:** Yes! The platform supports multilingual training. Ensure:
1. Your base model supports the target language (check model card)
2. Data is UTF-8 encoded
3. You have enough training examples (2x for non-English)

**Recommended models**:
- Multilingual: mBERT, XLM-RoBERTa
- German: GBERT, GPT-2-Wechsel
- Code: CodeLLaMA, StarCoder

### Q9: How do I structure my dataset for fine-tuning?

**A:** Format depends on task:

**Chatbot (JSONL)**:
```json
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]}
```

**Classification (CSV)**:
```csv
text,label
"Great product!","positive"
"Terrible service","negative"
```

**Code (JSONL)**:
```json
{"instruction": "Reverse a string", "code": "def reverse(s): return s[::-1]"}
```

See [Use-Case Templates](use-cases/) for detailed examples.

### Q10: Can I use data from the internet?

**A:** Be careful:
- ✅ Public datasets (Kaggle, HuggingFace)
- ✅ Open-source repositories
- ⚠️ Scraped data (check robots.txt and terms of service)
- ❌ Copyrighted material without permission
- ❌ Personal data without consent (GDPR compliance required)

**Tip**: Always cite data sources and check licenses.

### Q11: How do I split my dataset into train/validation/test?

**A:** Standard splits:
- **Training**: 80%
- **Validation**: 10% (for monitoring during training)
- **Test**: 10% (for final evaluation)

**Platform handles this automatically** if you upload a single dataset. Manual split:
```
dataset/
├── train/  (80%)
├── val/    (10%)
└── test/   (10%)
```

### Q12: My dataset has special characters (emojis, non-ASCII). Is that okay?

**A:** Yes! Ensure:
1. Files are UTF-8 encoded
2. Model tokenizer supports characters (most modern models do)
3. No control characters or invalid Unicode

Platform validates encoding on upload.

---

## Training Issues

### Q13: How long does training typically take?

**A:** Depends on:
- **Model size**: GPT-2 (125M) = 1-2 hours, LLaMA-7B = 8-12 hours
- **Dataset size**: 1,000 examples = 30 min, 100,000 = 10 hours
- **Hardware**: 1 GPU vs 4 GPUs vs 8 GPUs
- **Configuration**: LoRA (fast) vs full fine-tuning (slow)

**Typical times (4x A100 GPUs, LoRA)**:
- Small model + small data: 30 minutes - 2 hours
- Medium model + medium data: 4-8 hours
- Large model + large data: 12-24 hours

### Q14: My training loss isn't decreasing. What's wrong?

**A:** Troubleshooting steps:

**1. Check learning rate**:
- Too high (>1e-3): Loss explodes or NaN
- Too low (<1e-6): No progress
- **Try**: 5e-5 (good starting point)

**2. Verify dataset**:
- Check validation report for errors
- Ensure labels are correct
- Remove duplicates

**3. Adjust batch size**:
- Too small (<4): Noisy updates
- **Try**: 8-16 with gradient accumulation

**4. Check convergence time**:
- Some models need 500+ steps to show progress
- Let it run longer before stopping

### Q15: I got "CUDA out of memory" error. How do I fix it?

**A:** **Immediate fixes**:

1. **Reduce batch size**: Try 1 or 2
2. **Enable gradient checkpointing**:
   ```yaml
   gradient_checkpointing: true
   ```
3. **Use LoRA** instead of full fine-tuning
4. **Reduce sequence length**:
   ```yaml
   max_length: 512  # instead of 2048
   ```

**Long-term solutions**:
- Use smaller base model
- Request more GPUs
- Use FSDP for very large models

See [Troubleshooting Guide](TROUBLESHOOTING.md#gpu-out-of-memory) for details.

### Q16: Can I pause and resume training?

**A:** Yes!

**To pause**:
1. Go to Training → Your Job
2. Click **Pause** button
3. Current state saved as checkpoint

**To resume**:
1. Go to Training → Paused Jobs
2. Click **Resume**
3. Training continues from last checkpoint

**Note**: Paused jobs keep GPU allocation for 1 hour, then released.

### Q17: My validation loss is much higher than training loss. What does this mean?

**A:** This is **overfitting** - model memorized training data but can't generalize.

**Solutions**:
1. **Get more data** (best solution)
2. **Add regularization**:
   ```yaml
   weight_decay: 0.01
   dropout: 0.1
   ```
3. **Early stopping**: Stop when validation loss stops improving
4. **Reduce model capacity**: Use smaller model or LoRA with lower rank
5. **Data augmentation**: Add variations to training data

### Q18: How do I know when to stop training?

**A:** Stop when:
- ✅ Validation loss plateaus for 3+ epochs
- ✅ Validation loss starts increasing (overfitting)
- ✅ Model outputs look good qualitatively
- ✅ Reached your time/budget limit

**Don't stop** just because:
- ❌ Training loss is still decreasing (check validation!)
- ❌ You've hit a preset number of epochs (might need more)

**Use early stopping** (automatic):
```yaml
early_stopping:
  enabled: true
  patience: 3
  monitor: "val_loss"
```

### Q19: Can I train on multiple datasets at once?

**A:** Yes! Two options:

**1. Merge datasets** (recommended):
- Combine before upload
- Platform treats as single dataset
- Easier to manage

**2. Multi-task learning** (advanced):
- Upload datasets separately
- Use custom training script
- Specify task indicators in data

Example merged dataset:
```json
{"text": "Customer question", "label": "support", "source": "dataset1"}
{"text": "Code problem", "label": "technical", "source": "dataset2"}
```

### Q20: What's the difference between epochs and steps?

**A:**

**Step**: One forward + backward pass through one batch
- Example: 100 examples, batch size 10 = 10 steps

**Epoch**: One complete pass through entire dataset
- Example: 1,000 examples, batch size 10 = 100 steps = 1 epoch

**What to configure**:
- For small datasets: Set epochs (e.g., 10 epochs)
- For large datasets: Set max steps (e.g., 10,000 steps)
- Platform converts between them automatically

---

## Model Testing

### Q21: How do I test my model after training?

**A:** Three methods:

**1. Quick Test** (simplest):
- Click **Test Model** in job card
- Enter input, get output instantly
- Good for quick checks

**2. Notebooks** (recommended):
- Navigate to Notebooks → New Notebook
- Load your model
- Run detailed experiments
- See [Student Handbook](STUDENT_HANDBOOK.md#testing-your-model)

**3. Batch Inference** (for many examples):
- Upload test CSV/JSONL
- Run batch job
- Download results

### Q22: My model outputs are repetitive or nonsensical. How do I fix this?

**A:** Adjust **generation parameters**:

**For repetitive outputs**:
```python
output = model.generate(
    prompt,
    repetition_penalty=1.2,  # Penalize repeats
    no_repeat_ngram_size=3,  # Avoid 3-gram repetition
)
```

**For nonsensical outputs**:
```python
output = model.generate(
    prompt,
    temperature=0.7,  # Lower = more focused (try 0.5-0.9)
    top_p=0.9,        # Nucleus sampling
    top_k=50,         # Limit vocabulary
)
```

**For too short outputs**:
```python
output = model.generate(
    prompt,
    min_length=50,    # Minimum tokens
    max_length=200,   # Maximum tokens
)
```

### Q23: Can I compare different checkpoints?

**A:** Yes!

**In Dashboard**:
1. Go to Training → Your Job → Checkpoints
2. Select multiple checkpoints
3. Click **Compare**
4. See metrics side-by-side

**In Notebooks**:
```python
# Load different checkpoints
model_v1 = load_model("checkpoint-500")
model_v2 = load_model("checkpoint-1000")
model_v3 = load_model("checkpoint-best")

# Test same prompt
prompt = "Write a poem about AI"
print("v1:", model_v1.generate(prompt))
print("v2:", model_v2.generate(prompt))
print("v3:", model_v3.generate(prompt))
```

### Q24: How do I export my model for use outside the platform?

**A:**

**Option 1: Download checkpoint** (preserves everything):
1. Go to Models → Your Model
2. Click **Download**
3. Select **Full Checkpoint** (includes optimizer state)
4. Use with PyTorch/HuggingFace transformers

**Option 2: Export for inference** (smaller):
1. Click **Export**
2. Select format:
   - HuggingFace (recommended)
   - ONNX (optimized)
   - TorchScript
3. Download

**Option 3: Push to HuggingFace Hub** (share publicly):
1. Connect HuggingFace account in Settings
2. Click **Push to Hub**
3. Set visibility (public/private)
4. Others can use: `transformers.AutoModel.from_pretrained("your-username/model-name")`

---

## Performance

### Q25: How can I make training faster?

**A:** Optimization strategies:

**Hardware**:
- ✅ Use more GPUs (linear speedup: 4 GPUs = 4x faster)
- ✅ Request A100 GPUs (2x faster than V100)

**Configuration**:
- ✅ Enable mixed precision: `precision: "bf16"`
- ✅ Increase batch size (if memory allows)
- ✅ Use LoRA instead of full fine-tuning (3-10x faster)
- ✅ Reduce max sequence length

**Data**:
- ✅ Use fewer but higher-quality examples
- ✅ Pre-process data to platform format
- ✅ Enable fast data loading: `num_workers: 8`

**Example config for maximum speed**:
```yaml
num_gpus: 4
mixed_precision: "bf16"
use_lora: true
gradient_checkpointing: false  # Faster but more memory
batch_size: 16
```

### Q26: How do I improve model quality?

**A:** Best practices:

**1. More/better data** (most important):
- Increase dataset size
- Improve data quality (remove noise)
- Balance classes
- Add diverse examples

**2. Longer training**:
- More epochs (but watch for overfitting)
- Lower learning rate for longer training

**3. Better base model**:
- Use larger model if quality insufficient
- Try model specifically pre-trained for your domain

**4. Hyperparameter tuning**:
- Learning rate: Try 1e-5, 5e-5, 1e-4
- LoRA rank: Try 16, 32, 64
- Batch size: Larger often better

**5. Ensemble methods**:
- Train multiple models
- Combine predictions

### Q27: What's the difference between LoRA and full fine-tuning?

**A:**

| Aspect | LoRA | Full Fine-tuning |
|--------|------|------------------|
| **Speed** | 3-10x faster | Slower |
| **Memory** | 90% less | Full model in memory |
| **Quality** | Very close (95-98%) | Slightly better |
| **File size** | 10-100 MB | 1-30 GB |
| **Use case** | Most scenarios | When max quality needed |
| **Trainable params** | 0.1-1% | 100% |

**Recommendation**: Start with LoRA. Only use full fine-tuning if:
- You have lots of GPUs and time
- Quality with LoRA insufficient
- Your task requires it (rare)

### Q28: Can I use multiple GPUs for faster training?

**A:** Yes! The platform automatically distributes across GPUs.

**How to enable**:
```yaml
num_gpus: 4  # Use 4 GPUs
```

**Speedup**:
- 1 → 2 GPUs: ~1.9x faster
- 1 → 4 GPUs: ~3.5x faster
- 1 → 8 GPUs: ~6x faster
(Not perfectly linear due to communication overhead)

**When to use**:
- ✅ Large models (>1B parameters)
- ✅ Large datasets
- ✅ Time constraints
- ❌ Small models (overhead not worth it)

Platform uses **Distributed Data Parallel (DDP)** automatically.

---

## Billing & Resources

### Q29: How much GPU time do I have?

**A:** Check your quota:
1. Navigate to Settings → Resource Usage
2. See:
   - GPU hours used this month
   - GPU hours remaining
   - Storage used
   - Active jobs

**Typical allocations**:
- Free tier: 50 GPU hours/month
- Student: 200 GPU hours/month
- Researcher: 500 GPU hours/month

**What's a GPU hour?**
- 1 GPU for 1 hour = 1 GPU hour
- 4 GPUs for 1 hour = 4 GPU hours
- 1 GPU for 30 minutes = 0.5 GPU hours

### Q30: What happens if I run out of GPU hours?

**A:**
1. **Warning at 80%**: Email notification
2. **Warning at 90%**: Dashboard alert
3. **At 100%**:
   - Current jobs continue to completion
   - Can't start new jobs
   - Can still access data and models

**Solutions**:
- Wait for monthly reset
- Request quota increase (Settings → Request More)
- Optimize jobs to use fewer hours
- Use checkpointing to avoid re-running failed jobs

### Q31: How can I reduce costs/GPU usage?

**A:**

**Before training**:
- Use smaller base model
- Enable LoRA
- Reduce epochs
- Use hyperparameter search on small subset first

**During training**:
- Monitor progress, stop early if not improving
- Use checkpointing (don't restart from scratch)
- Multi-task learning (train one model for multiple tasks)

**General**:
- Delete old models/checkpoints
- Use CPU for data preprocessing
- Share models with teammates (one training, all use)

---

## Security & Privacy

### Q32: Is my data private?

**A:** Yes:
- Your data is isolated per-user
- Other users cannot access your datasets
- Platform staff can access for debugging (with permission)
- Data not used to train platform models

**Compliance**:
- GDPR compliant
- Data residency: EU servers
- Encryption: at rest and in transit

### Q33: Can I share my model with other students?

**A:** Yes! Options:

**1. Within platform** (recommended):
- Go to Models → Your Model → Share
- Enter usernames to share with
- Set permissions (view only / can fine-tune)

**2. Export and share file**:
- Download checkpoint
- Share via file sharing service
- Others import: Upload → Import Model

**3. HuggingFace Hub**:
- Push to Hub (can be private)
- Share Hub link

### Q34: What data should I NOT upload?

**A:** Do not upload:
- ❌ Passwords, API keys, credentials
- ❌ Personal information (names, addresses, SSN) without anonymization
- ❌ Copyrighted material
- ❌ Illegal content
- ❌ Malicious code

**If you accidentally uploaded sensitive data**:
1. Delete dataset immediately
2. Email support@platform-url.com
3. Request data purge from backups

---

## Additional Questions

### Q35: Can I use custom models not in the list?

**A:** Yes! Two options:

**1. Request addition** (for popular models):
- Email support with model HuggingFace link
- Team evaluates and adds to platform

**2. Custom import** (advanced):
- Download model locally
- Upload to platform: Models → Import Custom
- Provide model architecture config

### Q36: What's the best way to learn the platform?

**A:**

**Recommended path**:
1. Read [Quick-start Guide](QUICKSTART.md) (30 min)
2. Complete built-in tutorial (Training → Tutorials) (1 hour)
3. Try sample datasets (Dashboard → Examples)
4. Read relevant use-case template (20 min)
5. Train your first model!
6. Refer to [Student Handbook](STUDENT_HANDBOOK.md) as needed

**Resources**:
- Video tutorials: Dashboard → Learn
- Office hours: Wednesdays 2-3 PM
- Discussion forum: Link in dashboard

---

## Still Have Questions?

**Can't find your answer?**

1. **Search handbook**: [Student Handbook](STUDENT_HANDBOOK.md) has detailed info
2. **Check troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md) for technical issues
3. **Community forum**: forum.platform-url.com
4. **Office hours**: Wednesdays 2-3 PM CET
5. **Email support**: support@platform-url.com

**Suggest a question**: If you think this FAQ should include something, email: docs@platform-url.com

---

*Last updated: January 12, 2025*
