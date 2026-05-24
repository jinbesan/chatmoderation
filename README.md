# AI Conflict Mediator

An intelligent chat moderation system that detects conflict in voice chat rooms and provides appropriate interventions to de-escalate situations without sounding robotic.

## Overview

The AI Conflict Mediator uses a two-agent architecture:
- **Agent 1 (Classifier)**: Analyzes chat messages to determine conflict severity and whether intervention is needed
- **Agent 2 (Intervention Writer)**: Generates natural-sounding responses to de-escalate conflicts when appropriate

The system includes features like intervention cooldowns, conflict cycle tracking, admin alerts, and blacklist word detection.

## Features

- Two-agent system for nuanced conflict detection and response
- Configurable intervention thresholds and cooldowns
- Admin alert system for moderator notifications
- Blacklist word detection with contextual weighting
- Conflict cycle tracking and automatic reset
- LLM provider flexibility (supports Groq, OpenAI, Anthropic, etc.)
- Natural-sounding interventions that match chat room register

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chatmoderation
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up your API key:
- For Groq (default): Set `GROQ_API_KEY` environment variable
- For other providers: See configuration section below

## Usage

### Running the Demo

The repository includes a demo script that shows how the mediator works with sample chat logs:

```bash
python examples/demo.py
```

Before running the demo, make sure you have set your API key:
```bash
# For Groq (default)
$env:GROQ_API_KEY="your-groq-api-key"  # PowerShell
# or
export GROQ_API_KEY="your-groq-api-key"  # Bash/Linux/macOS
```

The demo will process sample chat logs and show:
- When interventions are triggered
- What the AI says in response
- Admin alerts sent to moderators
- System state after each message

### Using the Mediator in Your Code

```python
from chatmoderation import create_mediator
import os
from datetime import datetime

# Create a mediator instance
mediator = create_mediator(
    api_key=os.getenv("GROQ_API_KEY"),  # or your provider's API key
    model="llama-3.1-8b-instant",       # optional, defaults to llama-3.1-8b-instant
    base_url="https://api.groq.com",    # optional, defaults to Groq
    room_name="Your Room Name",
    region="Your Region",
    admin_username="AdminUsername",
    admin_last_active=datetime(2026, 5, 14, 14, 2, 0),  # optional
    confidence_threshold=80.0,          # optional, defaults to 80.0
)

# Process chat messages
messages = [
    "[14:05:00] User1: Hello everyone!",
    "[14:05:05] User2: Hi there!",
    # ... more messages
]

for msg in messages:
    result = mediator.process_message(msg)
    
    if result:
        print(f"Intervention triggered!")
        if result.admin_alert:
            print(f"Admin Alert: {result.admin_alert}")
        if result.chat_message:
            print(f"AI Response: {result.chat_message}")
    else:
        print(f"No intervention needed for: {msg}")
    
    # Check system status
    status = mediator.get_status()
    print(f"Interventions so far: {status['intervention_count']}")
```

## Configuration

### LLM Provider Settings

The mediator is flexible and can work with various LLM providers that offer OpenAI-compatible APIs.

**Default Settings (Groq):**
- `base_url`: "https://api.groq.com"
- `model`: "llama-3.1-8b-instant"

**To use a different provider:**
```python
mediator = create_mediator(
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",  # OpenAI example
    model="gpt-4",                         # or your preferred model
    # ... other parameters
)
```

**Supported Providers:**
- Groq (default): base_url="https://api.groq.com"
- OpenAI: base_url="https://api.openai.com/v1"
- Anthropic: base_url="https://api.anthropic.com/v1" (if they offer OpenAI-compatible endpoint)
- Any other OpenAI-compatible API

### Mediator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | (required) | API key for your LLM provider |
| `model` | str | "llama-3.1-8b-instant" | Model name to use |
| `base_url` | str | "https://api.groq.com" | Base URL for the API |
| `room_name` | str | "Voice Chat Room" | Name of the chat room |
| `region` | str | "unknown" | Geographic/region identifier |
| `admin_username` | str | None | Username of the room admin |
| `admin_last_active` | datetime | None | Last time the admin was active |
| `confidence_threshold` | float | 80.0 | Minimum confidence % for intervention |
| `window_size` | int | 10 | Size of the rolling message window |

## How It Works

### Processing Flow

1. **Message Parsing**: Incoming chat messages are parsed into structured format
2. **Classification (Agent 1)**:
   - Message is analyzed with context (room stats, recent messages, severity trends)
   - Blacklist words are detected and counted
   - Severity level (None/Low/Medium/High) and confidence are determined
   - Intervention recommendation is made based on severity and confidence
3. **State Update**: Message and its classification are added to the system state
4. **Intervention Decision**:
   - If `intervention_needed` is true AND `confidence ≥ threshold`
   - AND intervention is allowed based on cooldowns and cycle limits
   - Then Agent 2 generates a response
5. **Response Generation (Agent 2)**:
   - Creates a natural-sounding chat message to de-escalate
   - Optionally generates an admin alert for moderators
   - Updates intervention state if a chat message was sent
6. **Admin Alerts**: Additional alerts may be sent based on severity trends and cooldowns

### Intervention Logic

- **Cooldown Period**: 2 minutes between interventions
- **Cycle Limits**: Maximum 2 interventions per conflict cycle
- **First Intervention**: Allows MEDIUM or HIGH severity
- **Second Intervention**: Allows only HIGH severity (after cooldown)
- **Cycle Reset**: Occurs when severity trend remains stable/deescalating for 3+ messages with None severity
- **Admin Alert Cooldown**: 5 minutes between admin alerts

## Demo Script Details

The `examples/demo.py` file includes three sample chat logs designed to test different scenarios:

1. **CHAT_LOG**: Immediate high-severity conflict with personal attacks
2. **CHAT_LOG_SLOW_BURN**: Gradual escalation from mild disagreement to hostility
3. **CHAT_LOG_BANTER**: Playful back-and-forth that should not trigger interventions
4. **CHAT_LOG_FAILED_DEESCALATION**: Attempts to de-escalate that fail
5. **CHAT_LOG_IMMEDIATE_HIGH**: Rapid escalation to high severity
6. **CHAT_LOG_SELF_RESOLVING**: Conflict that resolves on its own
7. **CHAT_LOG_MULTI_PARTY**: Multiple users involved in conflict

To test different logs, modify the `chat` variable in demo.py:
```python
# Select which chat log to test with by changing the variable below
chat = CHAT_LOG_IMMEDIATE_HIGH  # Change this to test different scenarios
```

## Extending the System

### Adding Custom Features

The system is designed to be extensible. You can:

1. **Modify Classification Logic**: Edit `agent1_classifier.py` to change how severity is determined
2. **Customize Interventions**: Edit `agent2_intervention.py` to change response generation
3. **Adjust Timing Parameters**: Modify `config.py` to change cooldowns, thresholds, etc.
4. **Add New Message Types**: Extend the parsing logic in `mediator.py` for different chat formats

### LLM Provider Integration

To add support for a new LLM provider:
1. Ensure the provider offers an OpenAI-compatible API endpoint
2. Set the appropriate `base_url` when creating the mediator
3. Specify the correct `model` name for that provider
4. The LLM client in `llm.py` handles the rest via the Groq SDK (which supports custom base URLs)

## Troubleshooting

### Common Issues

1. **API Authentication Errors**:
   - Verify your API key is correctly set in the environment
   - Check that you have sufficient quota/credits with your provider

2. **404 Errors**:
   - Ensure `base_url` is set correctly (should not include "/openai/v1" as the client adds it internally)
   - For Groq: use "https://api.groq.com"
   - For OpenAI: use "https://api.openai.com/v1"

3. **No Interventions Triggered**:
   - Check that your confidence threshold is not set too high
   - Verify that messages actually contain conflict signals
   - Ensure the rolling window has enough context (system needs at least 3 messages for trend analysis)

4. **Too Many Interventions**:
   - Verify cooldown periods are working correctly
   - Check that conflict cycle reset logic is functioning
   - Look at the severity trend calculations in state.py

### Getting Help

If you encounter issues:
1. Check the console output for debug messages (enabled in llm.py)
2. Review the system status via `mediator.get_status()`
3. Ensure all dependencies are installed correctly
4. Verify your API key and network connectivity

## License

[Specify your license here]

## Acknowledgments

- Thanks to the creators of the Groq API for providing fast LLM inference
- Built with Python and Pydantic for robust data validation