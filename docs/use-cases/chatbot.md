# Use Case: Chatbot Fine-tuning

**Complete guide to fine-tuning conversational AI models**

---

## Overview

This guide shows you how to fine-tune a language model for chatbot applications, including customer support, virtual assistants, domain-specific Q&A, and general conversation.

**What you'll learn**:
- Preparing dialogue datasets
- Recommended model configurations
- Training best practices
- Evaluation metrics
- Common pitfalls

**Time required**: 2-4 hours (training) + 1 hour (setup and evaluation)

---

## Use Cases

### 1. Customer Support Bot
- Answer frequently asked questions
- Provide product information
- Handle support tickets
- Route complex issues to humans

### 2. Domain Expert Assistant
- Medical information (non-diagnostic)
- Legal guidance (non-advisory)
- Technical documentation help
- Academic tutoring

### 3. Personal Assistant
- Schedule management
- Information lookup
- Task reminders
- General conversation

### 4. Internal Company Bot
- HR policy questions
- IT support
- Onboarding assistance
- Knowledge base access

---

## Dataset Format

### Required Format: JSONL (JSON Lines)

Each line is a complete conversation with alternating user and assistant messages.

**Basic format**:
```json
{"messages": [
  {"role": "system", "content": "You are a helpful customer support assistant."},
  {"role": "user", "content": "How do I reset my password?"},
  {"role": "assistant", "content": "To reset your password: 1) Click 'Forgot Password' on the login page 2) Enter your email 3) Check your inbox for a reset link 4) Follow the instructions in the email. Is there anything else I can help you with?"}
]}
```

**Multi-turn conversation**:
```json
{"messages": [
  {"role": "system", "content": "You are a helpful assistant for TechCorp support."},
  {"role": "user", "content": "Hi, my order hasn't arrived yet"},
  {"role": "assistant", "content": "I'd be happy to help track your order. Could you please provide your order number?"},
  {"role": "user", "content": "It's TC-12345"},
  {"role": "assistant", "content": "Thank you! Let me check that for you... I can see your order TC-12345 shipped on January 10th and is currently in transit. Expected delivery is January 15th. You can track it here: tracking.example.com/TC-12345"}
]}
```

### Dataset Structure

```
chatbot-training-data/
├── train.jsonl         # 80% of data (1000+ conversations)
├── validation.jsonl    # 10% of data (100+ conversations)
└── test.jsonl          # 10% of data (100+ conversations)
```

### System Prompts

Include a system message to define behavior:

**Customer support**:
```json
"You are a helpful and friendly customer support representative for [Company Name].
Be professional, empathetic, and solution-oriented.
If you don't know something, say so and offer to escalate."
```

**Technical assistant**:
```json
"You are an expert technical assistant specializing in [Domain].
Provide accurate, detailed explanations.
Use examples when helpful.
Ask clarifying questions if needed."
```

**Friendly chatbot**:
```json
"You are a friendly and engaging conversational AI.
Be helpful, curious, and maintain context throughout the conversation.
Show personality while remaining professional."
```

---

## Data Collection

### Sources

**1. Existing Support Tickets**:
```python
# Convert support tickets to dialogue format
import pandas as pd

tickets = pd.read_csv("support_tickets.csv")
dialogues = []

for _, row in tickets.iterrows():
    dialogue = {
        "messages": [
            {"role": "system", "content": "You are a support assistant."},
            {"role": "user", "content": row['customer_message']},
            {"role": "assistant", "content": row['support_response']}
        ]
    }
    dialogues.append(dialogue)

# Save as JSONL
import json
with open("train.jsonl", "w") as f:
    for d in dialogues:
        f.write(json.dumps(d) + "\n")
```

**2. FAQ Pages**:
Convert Q&A pairs to dialogue format:
```json
{"messages": [
  {"role": "user", "content": "What are your business hours?"},
  {"role": "assistant", "content": "We're open Monday-Friday 9 AM - 6 PM EST, and Saturday 10 AM - 4 PM EST. We're closed on Sundays and major holidays."}
]}
```

**3. Human Annotation**:
- Write example conversations
- Engage team members to create scenarios
- Use crowd-sourcing platforms

**4. Synthetic Data**:
```python
# Use GPT-4 to generate training examples
prompts = [
    "Generate a customer support conversation about returns",
    "Create a technical support dialogue about software installation",
    # ... more prompts
]
# Review and filter generated conversations
```

### Data Quality Checklist

✅ **Diverse topics**: Cover all areas bot should handle
✅ **Varied phrasing**: Multiple ways to ask same question
✅ **Realistic scenarios**: Based on actual user needs
✅ **Complete responses**: Thorough, helpful answers
✅ **Appropriate tone**: Matches your brand voice
✅ **Error handling**: Examples of "I don't know" responses
✅ **Multi-turn**: Some conversations should have >2 turns
✅ **Edge cases**: Unusual or complex situations

### Minimum Data Requirements

| Bot Complexity | Minimum Conversations | Recommended |
|----------------|----------------------|-------------|
| Simple FAQ | 100 | 500 |
| Customer Support | 500 | 2,000 |
| Domain Expert | 1,000 | 5,000 |
| General Chatbot | 5,000 | 20,000+ |

---

## Recommended Configuration

### Model Selection

**For simple FAQ/support (fast, efficient)**:
```yaml
model_name: "gpt2"  # or "gpt2-medium"
# Small, fast, good for straightforward Q&A
# Memory: ~2GB
# Training time: 1-2 hours
```

**For advanced conversation (better quality)**:
```yaml
model_name: "microsoft/phi-2"
# or "mistralai/Mistral-7B-v0.1"
# Better reasoning and context
# Memory: ~16GB
# Training time: 4-8 hours
```

**For production (highest quality)**:
```yaml
model_name: "meta-llama/Llama-2-7b-chat-hf"
# Pre-trained for conversation
# Excellent performance
# Memory: ~28GB with optimizations
# Training time: 8-12 hours
```

### Training Configuration

**Recommended settings** (works for most chatbots):

```yaml
# Model
model_name: "microsoft/phi-2"
use_lora: true
lora_config:
  r: 32
  alpha: 32
  dropout: 0.05
  target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

# Training
num_epochs: 3
learning_rate: 5e-5
lr_scheduler: "cosine"
warmup_steps: 100

# Batch size (adjust based on GPU)
per_device_train_batch_size: 4
gradient_accumulation_steps: 4  # Effective batch size: 16

# Optimization
mixed_precision: "bf16"
gradient_checkpointing: true
max_grad_norm: 1.0

# Data
max_length: 512  # Increase to 1024 for longer conversations
padding: "max_length"

# Saving
save_strategy: "steps"
save_steps: 500
save_total_limit: 3

# Evaluation
evaluation_strategy: "steps"
eval_steps: 250
load_best_model_at_end: true
metric_for_best_model: "eval_loss"

# Early stopping
early_stopping_patience: 3
```

### Configuration for Different Scales

**Small bot (< 500 conversations)**:
```yaml
num_epochs: 5  # More epochs for small data
learning_rate: 3e-5
weight_decay: 0.01  # More regularization
```

**Medium bot (500-5000 conversations)**:
```yaml
num_epochs: 3
learning_rate: 5e-5
# Use default settings above
```

**Large bot (> 5000 conversations)**:
```yaml
num_epochs: 2  # Less likely to overfit
learning_rate: 1e-4  # Can use higher LR
per_device_train_batch_size: 8  # Larger batches
```

---

## Training Process

### Step 1: Upload Dataset

1. Navigate to **Datasets** → **Upload New**
2. Select your `train.jsonl` file
3. Enter metadata:
   - Name: `customer-support-chatbot-v1`
   - Description: `Customer support conversations for product X`
   - Type: `Dialogue/Chat`
4. Upload validation and test sets (optional but recommended)
5. Wait for validation to complete

### Step 2: Configure Training

1. Go to **Training** → **New Job**
2. Select template: **Chatbot Fine-tuning**
3. Choose your dataset
4. Select base model (e.g., `microsoft/phi-2`)
5. Review configuration (or use advanced settings)
6. Name your job: `chatbot-support-v1`

### Step 3: Monitor Training

Watch these metrics:
- **Training Loss**: Should decrease steadily
- **Validation Loss**: Should decrease and stay close to training loss
- **Perplexity**: Lower is better (good: <20, excellent: <10)

**Expected timeline** (4x A100 GPUs):
- Small model (GPT-2): 1-2 hours
- Medium model (Phi-2): 4-6 hours
- Large model (Llama-7B): 8-12 hours

### Step 4: Evaluate Results

Once training completes, test your model:

**Quick test**:
```python
# In notebook
from agent4_inference import load_model

model = load_model("checkpoint-best")

# Test simple query
response = model.generate("How do I reset my password?")
print(response)

# Test multi-turn
conversation = [
    {"role": "user", "content": "Hi, I need help with my order"},
]
response = model.generate_conversation(conversation)
print(response)
```

---

## Evaluation Metrics

### Automated Metrics

**1. Perplexity** (most important):
```python
# Lower = better
# Good: < 20
# Excellent: < 10
```

**2. BLEU Score** (if you have reference responses):
```python
from datasets import load_metric
bleu = load_metric("bleu")

predictions = ["Your order will arrive tomorrow"]
references = [["Your order will be delivered tomorrow"]]
score = bleu.compute(predictions=predictions, references=references)
# Good: > 0.3
```

**3. Response Length**:
```python
# Check average response length
avg_length = sum(len(r.split()) for r in responses) / len(responses)
# Should match your training data distribution
```

### Human Evaluation

**Test scenarios** (create 20-30):
```yaml
scenarios:
  - query: "How do I return a product?"
    expected: "Should provide clear return steps"

  - query: "What's your refund policy?"
    expected: "Should explain policy accurately"

  - query: "Tell me about quantum physics"
    expected: "Should stay on topic or politely decline"
```

**Evaluation criteria**:
- ✅ **Relevance**: Answers the question asked
- ✅ **Accuracy**: Information is correct
- ✅ **Completeness**: Provides all necessary details
- ✅ **Tone**: Matches brand voice
- ✅ **Safety**: No harmful/inappropriate content
- ✅ **Helpfulness**: Actually solves user's problem

**Scoring**:
```
5 = Perfect response
4 = Good response, minor issues
3 = Acceptable, but could be better
2 = Poor response, major issues
1 = Unacceptable

Target: Average score ≥ 4.0
```

---

## Common Pitfalls & Solutions

### Problem 1: Bot Repeats Training Examples Verbatim

**Symptom**: Model outputs exact conversations from training data

**Cause**: Overfitting, memorization

**Solution**:
```yaml
# Increase regularization
weight_decay: 0.01
dropout: 0.1

# Get more diverse data
# Add data augmentation

# Early stopping
early_stopping_patience: 2
```

### Problem 2: Responses Are Too Short

**Symptom**: Bot gives one-sentence answers when more detail needed

**Cause**: Training data has short responses, or generation parameters too restrictive

**Solution**:
```python
# Adjust generation parameters
response = model.generate(
    prompt,
    min_length=30,      # Force minimum length
    max_length=200,
    length_penalty=0.8,  # Slight preference for longer
)

# Or improve training data with longer responses
```

### Problem 3: Bot Goes Off-Topic

**Symptom**: Model discusses irrelevant topics

**Cause**: Base model knowledge dominating, insufficient fine-tuning

**Solution**:
```yaml
# More training epochs
num_epochs: 5

# Include more diverse training examples
# showing appropriate scope

# Stronger system prompts
"You are a customer support assistant.
ONLY answer questions about [specific topics].
For other topics, politely redirect to appropriate resources."
```

### Problem 4: Inconsistent Personality

**Symptom**: Tone varies from formal to casual randomly

**Cause**: Inconsistent training data

**Solution**:
- Review and normalize training data tone
- Use consistent system prompts
- Add examples showing desired personality

### Problem 5: Can't Handle Multi-Turn

**Symptom**: Bot forgets context from previous messages

**Cause**: Not enough multi-turn examples, or context length too short

**Solution**:
```yaml
# Increase context window
max_length: 1024  # from 512

# Add more multi-turn training examples
# Ensure conversation history included in prompts
```

---

## Deployment Checklist

Before deploying your chatbot:

✅ **Accuracy test**: 90%+ correct responses on test set
✅ **Safety test**: No harmful outputs on adversarial prompts
✅ **Edge cases**: Tested unusual/unexpected inputs
✅ **Multi-turn**: Maintains context across 3+ turns
✅ **Response time**: < 2 seconds average
✅ **Fallback**: Gracefully handles unknown questions
✅ **Human handoff**: Can escalate to human when needed
✅ **Monitoring**: Logging and analytics in place

---

## Advanced Tips

### Personality Tuning

Make your bot more engaging:

```json
{"messages": [
  {"role": "system", "content": "You are a friendly, enthusiastic tech support agent named Alex. Use emojis occasionally 😊 and show genuine interest in helping users. Keep responses conversational but professional."},
  {"role": "user", "content": "My app isn't working"},
  {"role": "assistant", "content": "Oh no! 😟 I'm sorry you're having trouble with the app. I'd love to help you get this sorted out! Can you tell me what exactly happens when you try to use it? Does it crash, freeze, or show an error message?"}
]}
```

### Few-Shot Learning

Include examples in system prompt:

```json
{"role": "system", "content": "You are a support assistant. Here are examples:\n\nUser: How do I cancel?\nAssistant: To cancel your subscription: 1) Log into your account 2) Go to Settings → Billing 3) Click 'Cancel Subscription' 4) Confirm cancellation. You'll retain access until your current period ends.\n\nUser: Forgot password\nAssistant: I can help with that! Click 'Forgot Password' on the login page, enter your email, and you'll receive a reset link within 5 minutes. Check your spam folder if you don't see it. Need anything else?"}
```

### Knowledge Injection

Add company-specific knowledge:

```json
{"messages": [
  {"role": "system", "content": "You are a support agent for TechCorp. Key facts: Founded 2020, main product is CloudSync, pricing starts at $9/month, support hours are 9 AM-6 PM EST Monday-Friday, enterprise support available 24/7."},
  {"role": "user", "content": "When is support available?"},
  {"role": "assistant", "content": "Our support team is available Monday through Friday, 9 AM to 6 PM EST. If you're an Enterprise customer, you have access to 24/7 priority support! 🎉"}
]}
```

---

## Example Dataset

**Download**: [customer-support-example.jsonl](../examples/customer-support-example.jsonl)

**Contains**:
- 1,000 customer support conversations
- Multiple domains (returns, technical support, billing)
- Mix of simple and complex queries
- Multi-turn dialogues
- Various tones and styles

**To use**:
1. Download file
2. Upload to platform: Datasets → Upload
3. Follow this guide to fine-tune

---

## Resources

**Sample datasets**:
- [Customer Support Dataset](../examples/datasets/customer-support.jsonl)
- [FAQ Dataset](../examples/datasets/faq-bot.jsonl)
- [Technical Support](../examples/datasets/tech-support.jsonl)

**Templates**:
- [Basic chatbot config](../examples/configs/chatbot-basic.yaml)
- [Advanced chatbot config](../examples/configs/chatbot-advanced.yaml)

**Further reading**:
- [Student Handbook - Testing Models](../STUDENT_HANDBOOK.md#testing-your-model)
- [Deployment Guide](../deployment/chatbot-deployment.md)
- [Prompt Engineering Tips](../advanced/prompt-engineering.md)

---

## Support

**Questions?**
- Forum: forum.platform-url.com/c/chatbots
- Slack: #chatbot-fine-tuning
- Email: support@platform-url.com

**Report issues with this guide**:
- GitHub: github.com/platform/docs/issues
- Email: docs@platform-url.com

---

*Last updated: January 12, 2025*
