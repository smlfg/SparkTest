# Quick Start Guide

**Get started with the GPU Training Platform in under 30 minutes!**

This guide walks you through your first fine-tuning job from login to testing your model.

---

## What You'll Need

- ✅ Platform credentials (email + password)
- ✅ Web browser (Chrome, Firefox, or Edge)
- ✅ Sample dataset (we provide one!)
- ⏱️ 30 minutes of your time

---

## Step 1: Log In (2 minutes)

### Access the Platform

1. **Open your browser** and navigate to:
   ```
   http://your-platform-url:8002
   ```

2. **Enter your credentials**:
   - Username: `your-username` (provided by instructor)
   - Password: `your-password` (sent to your email)

3. **First-time login**:
   - Change your password when prompted
   - Set up 2FA (recommended but optional)

4. **You're in!** You should see the main dashboard.

**Troubleshooting**:
- ❌ Can't connect? → Check VPN is connected
- ❌ Wrong password? → Click "Forgot Password"
- ❌ Blank page? → Try a different browser or clear cache

---

## Step 2: Download Sample Dataset (3 minutes)

We provide a ready-to-use sample dataset to get you started quickly.

### Option A: Use Built-in Sample (Easiest)

1. Navigate to **Datasets** → **Browse Samples**
2. Find "Customer Support Chatbot Sample"
3. Click **Use This Dataset**
4. ✅ Done! Skip to Step 3.

### Option B: Download and Upload

1. **Download sample dataset**:
   - [customer-support-sample.csv](http://platform-url:8002/samples/customer-support-sample.csv)
   - Or use the dashboard: **Help** → **Sample Datasets**

2. **Preview the data**:
   ```csv
   user_message,assistant_message
   "How do I reset my password?","Click 'Forgot Password', enter your email, and follow the link sent to you."
   "What are your business hours?","We're open Monday-Friday 9 AM - 6 PM EST."
   ```

3. **Upload to platform**:
   - Navigate to **Datasets** → **Upload New**
   - Click **Choose File** → Select `customer-support-sample.csv`
   - Fill in details:
     - **Name**: `my-first-dataset`
     - **Description**: `Sample customer support conversations`
     - **Type**: `Dialogue/Chat`
   - Click **Upload**

4. **Wait for processing** (~1 minute)
   - Status changes from "Processing" → "Ready" ✅
   - You'll see: "100 examples validated successfully"

---

## Step 3: Start Your First Training Job (5 minutes)

Now for the exciting part - train your first model!

### Launch Training

1. **Navigate to**: **Training** → **New Job**

2. **Select template**: Click **Chatbot Fine-tuning**
   - This pre-configures everything for conversational AI

3. **Configure job** (most are pre-filled):

   **Basic Settings**:
   - **Job Name**: `my-first-chatbot`
   - **Dataset**: Select `my-first-dataset` (or the sample)
   - **Base Model**: Leave default `gpt2` (fast for learning)

   **Training Parameters** (can use defaults):
   ```
   Epochs: 3
   Learning Rate: 5e-5
   Batch Size: 8
   GPUs: 1
   ```

   **Estimated time**: ~30 minutes
   **Estimated cost**: 0.5 GPU hours

4. **Review and launch**:
   - Click **Review Configuration**
   - Check everything looks right
   - Click **Start Training** 🚀

5. **Confirmation**:
   - You'll see: "Training job started successfully!"
   - Job ID: `job-12345`
   - Status: "Initializing..."

---

## Step 4: Monitor Training (20 minutes)

While your model trains, let's watch the progress!

### Real-Time Dashboard

You'll automatically be taken to the training dashboard. Here's what you see:

**Progress Panel** (top):
```
Job: my-first-chatbot
Status: Training
Progress: [████████░░░░░░░░] 45% (Step 450/1000)
Time Elapsed: 00:15:23
ETA: 00:18:30
```

**Metrics Chart** (center):
Live graphs showing:
- **Training Loss**: Should go down (Good: decreasing steadily)
- **Validation Loss**: Should also go down (Watch for it diverging)
- **Learning Rate**: Follows schedule

**GPU Stats** (right):
```
GPU 0: 95% utilization
Memory: 12.5 GB / 40 GB
Temperature: 72°C (normal)
```

### What to Watch For

✅ **Good signs**:
- Loss decreasing over time
- GPU utilization >80%
- Smooth progress (no long pauses)

⚠️ **Warning signs**:
- Loss = NaN or Infinity → See [Troubleshooting Guide](TROUBLESHOOTING.md#training-loss-is-nan)
- Stuck at 0% for >5 min → Refresh page
- GPU 0% → Contact support

### Take a Break! ☕

Training takes ~30 minutes. Perfect time to:
- Read the [Student Handbook](STUDENT_HANDBOOK.md)
- Explore the dashboard
- Grab coffee/tea

You'll get a notification when training completes!

---

## Step 5: Test Your Model (5 minutes)

Training complete? Let's see what your model can do!

### Quick Test (In Dashboard)

1. **When training finishes**, you'll see:
   ```
   ✅ Training completed successfully!
   Final Loss: 0.45
   Best Checkpoint: checkpoint-1000
   ```

2. **Click "Test Model"** button

3. **Interactive Test Interface** opens:
   ```
   Enter your message:
   [_______________________________________________]

   [Generate Response]
   ```

4. **Try some examples**:

   **Example 1**:
   ```
   You: How do I reset my password?

   Bot: To reset your password, click on the 'Forgot Password'
   link on the login page, enter your email address, and you'll
   receive instructions within a few minutes.
   ```

   **Example 2**:
   ```
   You: What are your business hours?

   Bot: We're open Monday through Friday from 9 AM to 6 PM EST.
   We're closed on weekends and major holidays.
   ```

   **Example 3** (test something not in training):
   ```
   You: Tell me about quantum physics

   Bot: I apologize, but I'm designed to help with customer
   support questions. For questions about quantum physics,
   I'd recommend checking educational resources or consulting
   a science expert.
   ```

5. **Adjust generation settings** (optional):
   ```
   Temperature: 0.7 (higher = more creative)
   Max Length: 100 tokens
   ```

### Advanced Testing (In Notebooks)

Want more control? Use Jupyter notebooks:

1. **Navigate to**: **Notebooks** → **New Notebook**

2. **Select template**: "Model Testing"

3. **Notebook opens** with your model pre-loaded:
   ```python
   # Your model is already loaded as 'model'
   response = model.generate("How do I contact support?")
   print(response)
   ```

4. **Try different prompts**:
   ```python
   test_prompts = [
       "What is your refund policy?",
       "How do I track my order?",
       "Can I change my delivery address?"
   ]

   for prompt in test_prompts:
       response = model.generate(prompt)
       print(f"Q: {prompt}")
       print(f"A: {response}\n")
   ```

---

## Step 6: What's Next?

Congratulations! 🎉 You've successfully:
- ✅ Logged into the platform
- ✅ Uploaded a dataset
- ✅ Trained your first model
- ✅ Tested the results

### Improve Your Model

Want better results? Try:

**1. More training data**:
   - Current: 100 examples
   - Better: 500-1,000 examples
   - Upload your own data: [See data preparation guide](STUDENT_HANDBOOK.md#uploading-datasets)

**2. Better base model**:
   - Current: GPT-2 (124M parameters)
   - Better: Phi-2 (2.7B) or Mistral-7B
   - Change in: Training → Model Selection

**3. More training**:
   - Current: 3 epochs
   - Try: 5-10 epochs (watch for overfitting)
   - Adjust in: Training → Parameters

**4. Fine-tune parameters**:
   - Learning rate: Try 1e-5, 3e-5, or 1e-4
   - Batch size: Larger = more stable (if GPU allows)
   - See: [Advanced Configuration](STUDENT_HANDBOOK.md#advanced-configuration)

### Try Different Use Cases

Explore other templates:

**Text Classification**:
- Sentiment analysis
- Topic categorization
- Intent detection
- [Full guide](use-cases/classifier.md)

**Code Generation**:
- Function generation
- Code completion
- Bug fixing
- [Full guide](use-cases/code-assistant.md)

**Image Generation** (Advanced):
- FLUX.1 LoRA fine-tuning
- Custom style transfer
- Requires more GPU time

### Learn More

**Documentation**:
- 📖 [Student Handbook](STUDENT_HANDBOOK.md) - Complete guide (1 hour read)
- ❓ [FAQ](FAQ.md) - Quick answers to common questions
- 🔧 [Troubleshooting](TROUBLESHOOTING.md) - Fix common issues
- 📋 [Use Case Templates](use-cases/) - Detailed guides for specific tasks

**Get Help**:
- 💬 Forum: forum.platform-url.com
- 💬 Slack: #gpu-training-students
- 📅 Office Hours: Wednesdays 2-3 PM CET
- ✉️ Email: support@platform-url.com

**Video Tutorials**:
- Platform Overview (5 min)
- Your First Fine-Tune (10 min) - *what you just did!*
- Advanced Configuration (15 min)
- Access: Dashboard → **Learn** → **Videos**

---

## Common Next Questions

### How do I use my model in production?

**Option 1: Platform API** (easiest):
```python
import requests

response = requests.post(
    "http://platform-url:8005/api/v1/inference",
    json={
        "model": "my-first-chatbot",
        "prompt": "How do I reset my password?"
    }
)
print(response.json()['generated_text'])
```

**Option 2: Export model**:
1. Models → Your Model → Export
2. Download checkpoint
3. Use with HuggingFace transformers locally

[Full deployment guide](STUDENT_HANDBOOK.md#deployment)

### How much does it cost?

**Free tier**:
- 50 GPU hours/month
- 10 GB storage
- Perfect for learning!

**This tutorial used**: ~0.5 GPU hours

**Typical costs**:
- Small chatbot (like this): 0.5-1 GPU hours
- Medium chatbot: 5-10 GPU hours
- Large model: 20-50 GPU hours

Check usage: Dashboard → Settings → **Resource Usage**

### Can I share my model?

Yes! Multiple ways:

**1. Share within platform**:
- Models → Share → Enter username

**2. Export and share file**:
- Models → Download → Share file

**3. Push to HuggingFace** (public):
- Models → Push to Hub → Set public/private

### What if something went wrong?

**Common issues**:

**Training failed**:
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Most common: GPU memory (reduce batch size)
- Email logs to: support@platform-url.com

**Model outputs bad responses**:
- Need more/better training data
- Try different base model
- Increase epochs

**Can't log in**:
- VPN connected?
- Correct URL?
- Password reset: Login page → Forgot Password

**Still stuck?**
- Office Hours: Wed 2-3 PM
- Email: support@platform-url.com (include Job ID)

---

## Checklist: Did You Complete Everything?

Go through this checklist to confirm:

- [ ] Logged into platform successfully
- [ ] Uploaded or selected sample dataset
- [ ] Started training job (job name: `_________`)
- [ ] Monitored training to completion
- [ ] Tested model with at least 3 different prompts
- [ ] Understood what to try next

**All checked?** Amazing! You're ready to build real AI models! 🚀

---

## Next Steps by Goal

**I want to build a chatbot for my project**:
→ Read [Chatbot Use Case Guide](use-cases/chatbot.md)
→ Prepare your own dataset (500+ conversations)
→ Fine-tune on better base model (Phi-2 or Mistral)

**I need to classify text**:
→ Read [Classification Use Case Guide](use-cases/classifier.md)
→ Prepare labeled dataset (500+ examples per class)
→ Use BERT-based models

**I want to generate code**:
→ Read [Code Assistant Guide](use-cases/code-assistant.md)
→ Use CodeGen or Code Llama models
→ Prepare code examples with instructions

**I'm just learning/exploring**:
→ Try all templates with sample datasets
→ Read [Student Handbook](STUDENT_HANDBOOK.md)
→ Join community forum
→ Attend office hours

---

## Feedback

**Help us improve this guide!**

This is your first experience with the platform. What would make it better?

📝 **Quick survey** (2 min): http://platform-url/quickstart-survey

Or email: docs@platform-url.com

---

**Congratulations on completing the Quick Start! 🎉**

*You're now ready to build amazing AI applications!*

---

*Last updated: January 12, 2025*

*Questions? Contact: support@platform-url.com*
