# Student Handbook
## Your Complete Guide to GPU Training Platform

**Version 1.0** | Last Updated: January 2025

Welcome to the GPU Training Platform! This handbook will guide you through everything you need to know to successfully fine-tune machine learning models, from your first login to advanced optimization techniques.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Accessing the System](#accessing-the-system)
3. [Dashboard Overview](#dashboard-overview)
4. [Uploading Datasets](#uploading-datasets)
5. [Starting Fine-tuning](#starting-fine-tuning)
6. [Monitoring Your Training](#monitoring-your-training)
7. [Testing Your Model](#testing-your-model)
8. [Advanced Topics](#advanced-topics)
9. [FAQ](#faq)
10. [Getting Help](#getting-help)

---

## Getting Started

### What is This Platform?

The GPU Training Platform is a complete solution for fine-tuning large language models, image generation models, and other AI systems. Whether you're building a chatbot, a code assistant, or a custom classifier, this platform provides all the tools you need.

### What You'll Learn

By the end of this handbook, you'll be able to:
- Upload and prepare datasets for training
- Configure and launch training jobs
- Monitor training progress in real-time
- Test your models using interactive notebooks
- Deploy models for inference
- Troubleshoot common issues

### Prerequisites

**Required:**
- Basic understanding of machine learning concepts
- Familiarity with Python (for advanced features)
- Your platform credentials (provided by your administrator)

**Recommended:**
- Understanding of neural networks
- Experience with PyTorch or TensorFlow
- Basic Linux command-line knowledge

### System Overview

The platform consists of six integrated agents:

1. **Agent 1**: Multi-node orchestration and network management
2. **Agent 2**: Web-based dashboard (your main interface)
3. **Agent 3**: Training orchestration and job management
4. **Agent 4**: Interactive Jupyter notebooks for testing
5. **Agent 5**: Model inference and deployment
6. **Agent 6**: Documentation and support (this handbook)

---

## Accessing the System

### Initial Login

1. **Open your web browser** (Chrome, Firefox, or Safari recommended)
2. **Navigate to**: `http://your-platform-url:8002`
3. **Enter your credentials**:
   - Username: Provided by your administrator
   - Password: Sent to your email

4. **First-time setup**:
   - You'll be prompted to change your password
   - Set up two-factor authentication (recommended)
   - Configure your notification preferences

### SSH Access (Advanced)

For advanced users who need command-line access:

```bash
# Connect to the platform
ssh your-username@platform-hostname

# Navigate to your workspace
cd /workspace/users/your-username

# Check available GPUs
nvidia-smi
```

### VPN Configuration (If Required)

Some deployments require VPN access:

1. Download VPN configuration from dashboard (Settings → VPN)
2. Install OpenVPN client
3. Import configuration file
4. Connect before accessing platform

---

## Dashboard Overview

### Main Interface

When you log in, you'll see the main dashboard with several sections:

#### Navigation Bar (Top)
- **Home**: Overview of your projects
- **Datasets**: Manage training data
- **Training**: Start and monitor jobs
- **Models**: Browse trained models
- **Notebooks**: Interactive testing environment
- **Settings**: Account and preferences

#### Quick Actions Panel (Left)
- New Training Job
- Upload Dataset
- Open Notebook
- Deploy Model
- View Documentation

#### Status Panel (Right)
- GPU Availability
- Active Jobs
- Recent Activity
- System Health

#### Main Content Area (Center)
- Your recent projects
- Training job cards
- Performance metrics
- Quick-start tutorials

### Understanding the Interface

**Project Cards**: Each card represents a training project:
- Project name and description
- Current status (Running, Completed, Failed)
- Progress bar and metrics
- Quick action buttons

**Color Coding**:
- 🟢 Green: Successful/Running
- 🟡 Yellow: Pending/Queued
- 🔴 Red: Failed/Error
- ⚪ Gray: Stopped/Archived

### Customizing Your Dashboard

1. Click **Settings** → **Dashboard Layout**
2. Drag and drop widgets to rearrange
3. Show/hide panels based on your needs
4. Save your preferred layout

---

## Uploading Datasets

### Dataset Requirements

Your dataset must meet these requirements:

**Format Options**:
- **Text Files**: `.txt`, `.csv`, `.json`, `.jsonl`
- **Images**: `.jpg`, `.png` (for image models)
- **Archives**: `.zip`, `.tar.gz` (will be extracted)

**Size Limits**:
- Single file: 10 GB max
- Total dataset: 100 GB max
- Contact admin for larger datasets

**Structure**:
```
dataset/
├── train/
│   ├── file1.txt
│   ├── file2.txt
│   └── ...
├── validation/
│   ├── file1.txt
│   └── ...
└── test/ (optional)
    └── ...
```

### Upload Methods

#### Method 1: Web Upload (Recommended for Small Datasets)

1. Navigate to **Datasets** → **Upload New**
2. Click **Choose Files** or drag-and-drop
3. Enter dataset metadata:
   - Name: `my-training-data`
   - Description: Brief explanation
   - Type: Text/Image/Code
   - License: (if applicable)
4. Click **Upload**
5. Wait for processing (automatic validation)

#### Method 2: Command Line (For Large Datasets)

```bash
# Connect via SSH
ssh your-username@platform-hostname

# Create dataset directory
mkdir -p /workspace/data/my-dataset

# Upload using SCP
scp -r local-dataset-folder/ your-username@platform-hostname:/workspace/data/my-dataset/

# Or use rsync for resume capability
rsync -avz --progress local-dataset/ your-username@platform-hostname:/workspace/data/my-dataset/
```

#### Method 3: Cloud Import

1. Navigate to **Datasets** → **Import from Cloud**
2. Select provider: AWS S3, Google Cloud, Azure
3. Enter bucket/container details
4. Configure authentication
5. Select files to import
6. Click **Start Import**

### Dataset Formats

#### Chat/Dialogue Data

**JSONL Format** (Recommended):
```json
{"messages": [
  {"role": "user", "content": "Hello, how are you?"},
  {"role": "assistant", "content": "I'm doing well, thank you!"}
]}
{"messages": [
  {"role": "user", "content": "What's the weather?"},
  {"role": "assistant", "content": "I don't have access to weather data."}
]}
```

**CSV Format**:
```csv
user_message,assistant_message
"Hello, how are you?","I'm doing well, thank you!"
"What's the weather?","I don't have access to weather data."
```

#### Text Classification

```json
{"text": "This product is amazing!", "label": "positive"}
{"text": "Terrible experience", "label": "negative"}
{"text": "It's okay, nothing special", "label": "neutral"}
```

#### Code Generation

```json
{"instruction": "Write a function to reverse a string", "code": "def reverse(s):\n    return s[::-1]"}
{"instruction": "Create a binary search function", "code": "def binary_search(arr, x):\n    ..."}
```

#### Image Training (FLUX/Stable Diffusion)

```
images/
├── instance_images/
│   ├── subject_001.jpg  (your subject)
│   ├── subject_002.jpg
│   └── ...
├── captions.txt
└── metadata.json
```

### Dataset Validation

After upload, the platform automatically validates your dataset:

**Validation Checks**:
- ✓ File format correctness
- ✓ Required fields present
- ✓ Encoding (UTF-8)
- ✓ No corrupted files
- ✓ Reasonable size distribution
- ✓ No duplicate entries

**Review Validation Report**:
1. Go to **Datasets** → Your Dataset
2. Click **Validation Report**
3. Fix any warnings or errors
4. Re-upload if necessary

---

## Starting Fine-tuning

### Quick Start: One-Click Templates

The easiest way to start is using our pre-configured templates:

1. Navigate to **Training** → **New Job**
2. Select a template:
   - **Chatbot**: Conversational AI
   - **Text Classifier**: Sentiment analysis, categorization
   - **Code Assistant**: Code generation and completion
   - **Question Answering**: QA systems
   - **Image Generator**: Text-to-image (FLUX, Stable Diffusion)

3. Click **Use Template**
4. Configure basic settings:
   - Job name: `my-first-chatbot`
   - Dataset: Select from dropdown
   - Base model: Choose pre-trained model
5. Click **Start Training**

### Advanced Configuration

For more control, use advanced mode:

#### Step 1: Select Base Model

**Text Models**:
- GPT-2 (125M - 1.5B parameters)
- LLaMA 2/3 (7B - 70B parameters)
- Mistral (7B parameters)
- Phi-2 (2.7B parameters)

**Image Models**:
- FLUX.1 Dev (12B parameters)
- Stable Diffusion XL
- Stable Diffusion 1.5

**Consider**:
- Larger models = better quality but slower training
- Start with smaller models for testing
- Check GPU memory requirements

#### Step 2: Configure Training Parameters

**Basic Settings**:
```yaml
# Training Duration
epochs: 3                    # How many times to see full dataset
max_steps: 1000             # Or set maximum steps

# Learning Settings
learning_rate: 5e-5         # How fast the model learns
batch_size: 8               # Samples per training step
gradient_accumulation: 4    # Effective batch size multiplier

# Hardware
num_gpus: 4                 # GPUs to use (1-8)
mixed_precision: "bf16"     # Faster training, less memory
```

**Advanced Settings**:
```yaml
# Optimization
optimizer: "AdamW"
weight_decay: 0.01
warmup_steps: 100
lr_scheduler: "cosine"

# Memory Management
gradient_checkpointing: true
max_grad_norm: 1.0

# Monitoring
eval_steps: 100             # Validation frequency
save_steps: 500             # Checkpoint frequency
logging_steps: 10           # Log metrics every N steps
```

#### Step 3: Configure LoRA (Recommended)

LoRA (Low-Rank Adaptation) enables efficient fine-tuning with less memory:

```yaml
use_lora: true
lora_config:
  r: 32                     # Rank (higher = more capacity)
  alpha: 32                 # Scaling factor
  dropout: 0.05             # Regularization
  target_modules:           # Which layers to train
    - q_proj
    - v_proj
    - k_proj
    - o_proj
```

**Benefits**:
- 90% less memory usage
- 3x faster training
- Easy to share (small files)
- Can merge back to full model

#### Step 4: Review and Launch

1. Click **Review Configuration**
2. Check estimated:
   - Training time: ~4 hours
   - GPU hours: 16
   - Cost: (if applicable)
3. Verify dataset and parameters
4. Click **Launch Training Job**

### Multi-Node Training (Advanced)

For very large models or datasets:

1. Enable **Multi-Node Mode**
2. Select number of nodes: 2-8
3. Platform automatically:
   - Discovers available nodes (Agent 1)
   - Distributes training
   - Synchronizes checkpoints
4. Monitor all nodes from single dashboard

---

## Monitoring Your Training

### Real-Time Dashboard

Once training starts, you'll see:

#### Progress Panel
- **Current Step**: 450 / 1000
- **Epoch**: 1.5 / 3
- **Time Elapsed**: 02:34:12
- **ETA**: 01:45:30

#### Metrics Chart
Live updating graphs:
- Training Loss (should decrease)
- Validation Loss (should decrease)
- Learning Rate (follows schedule)
- GPU Utilization (should be high)
- Memory Usage (should be stable)

#### GPU Monitoring
- GPU 0: 95% utilization, 38GB / 40GB memory
- GPU 1: 94% utilization, 38GB / 40GB memory
- Temperature: 75°C (normal)
- Power: 350W / 400W

### Understanding Metrics

**Loss**: Measures model errors
- Lower = Better
- Should decrease over time
- Validation loss should track training loss
- ⚠️ If validation >> training: overfitting

**Perplexity**: For language models
- Lower = Better
- Measures prediction confidence
- Good: < 20, Excellent: < 10

**Accuracy**: For classifiers
- Higher = Better
- Training: Should approach 100%
- Validation: Your actual performance

### TensorBoard Integration

For detailed analysis:

1. Click **Open TensorBoard** in training job
2. Explore tabs:
   - **Scalars**: Loss and metrics over time
   - **Distributions**: Weight distributions
   - **Histograms**: Activation patterns
   - **Graphs**: Model architecture
   - **Text**: Sample outputs (if enabled)

### Log Viewer

Access raw training logs:

1. Click **View Logs** in job card
2. Filter by:
   - Level: INFO, WARNING, ERROR
   - Component: Trainer, Data, Model
   - Time Range
3. Download logs for offline analysis

### Checkpoints

Training saves checkpoints automatically:

**Checkpoint Strategy**:
- Every 500 steps
- End of each epoch
- Best model (by validation loss)
- Latest 3 checkpoints kept

**Managing Checkpoints**:
1. Navigate to job → **Checkpoints** tab
2. See all saved checkpoints
3. Download, delete, or resume from checkpoint

---

## Testing Your Model

### Quick Testing (WebUI)

Immediately after training completes:

1. Click **Test Model** in job card
2. Enter test input:
   - For chatbots: Type a message
   - For classifiers: Enter text to classify
   - For code: Describe what you want
3. Click **Generate**
4. View output and metrics

**Example - Chatbot**:
```
You: Hello! How can you help me today?

Bot: Hello! I'm a helpful AI assistant. I can help you with:
- Answering questions
- Providing information
- Having conversations
- And much more!

What would you like to know?
```

### Interactive Notebooks (Agent 4)

For detailed testing and experimentation:

1. Navigate to **Notebooks** → **New Notebook**
2. Select template: "Model Testing"
3. Notebook launches with pre-loaded model
4. Run cells to test different scenarios

**Sample Notebook Code**:
```python
# Load your fine-tuned model
from agent4_inference import load_model

model = load_model("checkpoint-1000")

# Test generation
prompt = "Write a story about a robot"
output = model.generate(
    prompt,
    max_length=200,
    temperature=0.7,
    top_p=0.9
)

print(output)
```

### Batch Testing

Test on multiple examples:

1. Prepare test file (CSV or JSONL)
2. Upload to **Notebooks** → **Data**
3. Run batch inference:

```python
import pandas as pd

# Load test data
test_data = pd.read_csv("test_examples.csv")

# Run predictions
results = []
for idx, row in test_data.iterrows():
    prediction = model.generate(row['input'])
    results.append({
        'input': row['input'],
        'expected': row['output'],
        'predicted': prediction
    })

# Analyze results
results_df = pd.DataFrame(results)
accuracy = (results_df['expected'] == results_df['predicted']).mean()
print(f"Accuracy: {accuracy:.2%}")
```

### Evaluation Metrics

The platform automatically computes:

**For Text Generation**:
- BLEU Score: Translation/generation quality
- ROUGE Score: Summarization quality
- Perplexity: Language modeling
- Human evaluation templates

**For Classification**:
- Accuracy
- Precision, Recall, F1
- Confusion Matrix
- ROC Curve

**For Code**:
- Pass@K: Code correctness
- Execution success rate
- Syntax error rate

---

## Advanced Topics

### Hyperparameter Tuning

Optimize your training configuration:

1. Navigate to **Training** → **Hyperparameter Search**
2. Define search space:
```yaml
learning_rate: [1e-5, 5e-5, 1e-4]
batch_size: [4, 8, 16]
lora_r: [16, 32, 64]
```
3. Select search strategy:
   - Grid Search: Try all combinations
   - Random Search: Random sampling
   - Bayesian Optimization: Smart search
4. Launch experiments
5. Review results and select best

### Custom Training Scripts

For maximum control:

1. Navigate to **Training** → **Custom Script**
2. Upload your training script:
```python
# train_custom.py
from playbooks.pytorch_fine_tune import PyTorchDistributedTrainer

# Your custom logic
trainer = PyTorchDistributedTrainer(args)
trainer.train(model, train_dataset, eval_dataset)
```
3. Configure environment
4. Launch job

### Model Merging

Combine multiple models or LoRA adapters:

1. Navigate to **Models** → **Merge**
2. Select base model
3. Add LoRA adapters with weights:
   - Chatbot LoRA: 0.5
   - Code LoRA: 0.5
4. Click **Merge**
5. Test merged model

### Distributed Training Strategies

For large models:

**Data Parallel (DP)**:
- Easiest to use
- Same model on each GPU
- Good for most cases

**Distributed Data Parallel (DDP)**:
- More efficient than DP
- Recommended for multi-GPU
- Automatic in platform

**Fully Sharded Data Parallel (FSDP)**:
- For models > 10B parameters
- Shards model across GPUs
- Enable in advanced settings

**Pipeline Parallel**:
- For extremely large models
- Different layers on different GPUs
- Use NeMo playbook

### Inference Optimization

Deploy faster models:

**Quantization**:
```python
# 8-bit quantization
model = load_model("checkpoint-1000", load_in_8bit=True)

# 4-bit quantization (smaller, faster)
model = load_model("checkpoint-1000", load_in_4bit=True)
```

**Benefits**:
- 4x smaller model size
- 2-3x faster inference
- Slight quality trade-off

**ONNX Export**:
1. Navigate to **Models** → Your Model → **Export**
2. Select format: ONNX
3. Configure optimization level
4. Download optimized model

### Experiment Tracking

Integrate with MLflow or Weights & Biases:

```python
# In your training config
monitoring:
  wandb:
    enabled: true
    project: "my-experiments"
    entity: "my-team"
```

**Features**:
- Compare experiments
- Track metrics
- Share results
- Collaborate with team

---

## FAQ

### Getting Started

**Q: I forgot my password. How do I reset it?**
A: Click "Forgot Password" on login page, or contact your administrator.

**Q: How do I know which GPU I'm using?**
A: Check the dashboard status panel or run `nvidia-smi` in a notebook.

**Q: Can I use the platform from home?**
A: Yes, if VPN is configured. Check with your administrator.

### Dataset Preparation

**Q: What's the best dataset size for fine-tuning?**
A: Minimum 100 examples, ideal 1,000-10,000. More data = better results.

**Q: Can I use data in languages other than English?**
A: Yes! Ensure your base model supports the language.

**Q: How do I handle imbalanced datasets?**
A: Use class weighting or data augmentation. See use-case templates.

### Training Issues

**Q: My training loss isn't decreasing. What's wrong?**
A: Common causes:
- Learning rate too high/low → Try 1e-5 to 1e-4
- Batch size too small → Increase with gradient accumulation
- Dataset issues → Validate your data

**Q: Training is very slow. How can I speed it up?**
A: Try:
- Enable mixed precision (bf16)
- Increase batch size
- Use LoRA instead of full fine-tuning
- Use more GPUs

**Q: I got "CUDA out of memory" error.**
A: Reduce:
- Batch size (try 1 or 2)
- Model size (use smaller base model)
- Sequence length
Enable:
- Gradient checkpointing
- LoRA

### Model Testing

**Q: How long does testing take?**
A: Inference: < 1 second per example. Batch testing: depends on dataset size.

**Q: Can I test before training finishes?**
A: Yes! Test intermediate checkpoints from the Checkpoints tab.

**Q: My model outputs are repetitive. How do I fix this?**
A: Adjust generation parameters:
- Increase temperature (0.7-1.0)
- Use top-p sampling (0.9)
- Add repetition penalty

### Performance

**Q: How do I know if my model is good enough?**
A: Compare:
- Validation loss to baseline
- Qualitative outputs
- Task-specific metrics
- Human evaluation

**Q: Can I continue training if results aren't good?**
A: Yes! Resume from last checkpoint with different parameters.

### Deployment

**Q: How do I share my model with others?**
A: Options:
1. Export and share checkpoint files
2. Deploy via Agent 5 inference API
3. Push to HuggingFace Hub (if permitted)

**Q: What's the difference between checkpoint and exported model?**
A: Checkpoint includes training state. Exported model is inference-only (smaller).

---

## Getting Help

### Support Channels

**Dashboard Help**:
- Click **?** icon in top-right corner
- Access context-sensitive help
- View video tutorials

**Documentation**:
- This handbook: Complete reference
- Quick-start guide: `docs/QUICKSTART.md`
- FAQ: `docs/FAQ.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- API reference: `docs/API_REFERENCE.md`

**Community**:
- Discussion forum: `forum.platform-url.com`
- Slack channel: #gpu-training-help
- Stack Overflow tag: [platform-name]

**Direct Support**:
- Email: support@platform-url.com
- Office hours: Mon-Fri 9AM-5PM CET
- Emergency: +49-XXX-XXXX (critical issues only)

### Reporting Issues

When reporting problems, include:

1. **Error Message**: Copy exact text
2. **Steps to Reproduce**: What you did
3. **Expected vs Actual**: What should happen vs what happened
4. **Environment**:
   - Browser version
   - Dataset size
   - Model configuration
5. **Screenshots**: If UI-related
6. **Logs**: Download from job → Logs

**Example Report**:
```
Subject: Training job stuck at 0% progress

Issue: My training job has been at 0% for 30 minutes

Steps:
1. Uploaded dataset "customer-support-chat" (500 examples)
2. Selected GPT-2 base model
3. Used "Chatbot" template
4. Clicked "Start Training"

Expected: Training should start within 5 minutes
Actual: Still shows "Initializing..." after 30 minutes

Environment:
- Browser: Chrome 120.0
- Dataset: 2.5 MB, JSONL format
- Config: Default chatbot template

Logs attached: training-job-12345.log
```

### Self-Service Resources

**Video Tutorials**: `http://localhost:11000/docs/videos`
- Platform Overview (5 min)
- Your First Fine-tune (10 min)
- Advanced Configuration (15 min)
- Troubleshooting (7 min)

**Interactive Tutorials**:
Available in dashboard → **Learn** section:
- Guided tour
- Sample datasets
- Pre-built examples
- Best practices guide

**Office Hours**:
Join weekly Q&A sessions:
- Wednesdays 2-3 PM CET
- Link: `zoom.us/platform-office-hours`
- No registration required

---

## Appendix

### Glossary

**Base Model**: Pre-trained model you start with (e.g., GPT-2, LLaMA)

**Checkpoint**: Saved model state during training

**Epoch**: One complete pass through training dataset

**Fine-tuning**: Adapting pre-trained model to specific task

**GPU**: Graphics Processing Unit (hardware for training)

**LoRA**: Low-Rank Adaptation (efficient fine-tuning method)

**Inference**: Using model to make predictions

**Overfitting**: Model memorizes training data, poor on new data

**Validation**: Testing on held-out data during training

### Keyboard Shortcuts

**Dashboard**:
- `Ctrl/Cmd + K`: Quick command search
- `G then D`: Go to Datasets
- `G then T`: Go to Training
- `G then N`: Go to Notebooks
- `?`: Show help

**Notebooks**:
- `Shift + Enter`: Run cell
- `A`: Insert cell above
- `B`: Insert cell below
- `D D`: Delete cell
- `Z`: Undo delete

### Resource Limits

**Free Tier**:
- 10 GB dataset storage
- 50 GPU hours/month
- 2 concurrent jobs
- 5 saved models

**Standard**:
- 100 GB dataset storage
- 200 GPU hours/month
- 5 concurrent jobs
- 20 saved models

**Premium**:
- Unlimited storage
- Unlimited GPU hours
- 10 concurrent jobs
- Unlimited models
- Priority support

### Contact Information

**Platform Team**:
- General inquiries: info@platform-url.com
- Technical support: support@platform-url.com
- Sales: sales@platform-url.com

**Address**:
GPU Training Platform
University Building, Room 123
12345 City, Germany

**Website**: `https://platform-url.com`

---

## Changelog

**Version 1.0** (January 2025)
- Initial release
- Complete student handbook
- All six agents documented
- Integration guides

---

**Thank you for using the GPU Training Platform!**

We're constantly improving. Share feedback: feedback@platform-url.com

*Last updated: January 12, 2025*
