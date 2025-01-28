# TaskMailerAI

TaskMailerAI is a Python application that processes emails using AI capabilities to handle various tasks and generate responses. The application monitors an email inbox for incoming messages and processes them based on predefined tasks, supporting both text and PDF output formats.

## Features

- Email-based task processing with AI integration
- Support for multiple AI providers (OpenAI, Azure OpenAI, and OpenRouter)
- Attachment processing (txt, md, csv, json, pdf, docx)
- Rate limiting for user requests
- PDF output generation
- Configurable task definitions
- User access control

## Prerequisites

- Python 3.x
- wkhtmltopdf (included in repository)
- Docker (for containerized deployment)

## Installation

### Local Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Deployment

The application is available as a Docker image on Docker Hub:

```bash
docker pull xnovakm4/taskmailerai
```

Run the container with mounted config directory:

```bash
docker run -d \
  -v /path/to/your/config:/app/config \
  xnovakm4/taskmailerai
```

## Configuration

The application requires two configuration files in the `config` directory:

### config.yaml

```yaml
email:
  imap_server: "imap.example.com"
  smtp_server: "smtp.example.com"
  email_address: "your-email@example.com"
  password: "your-email-password"

openrouter:
  api_key: "your-openrouter-api-key"

openai:
  api_key: "your-openai-api-key"

azure_openai:
  api_key: "your-azure-openai-api-key"
  endpoint: "your-azure-endpoint"
  api_version: "2023-12-01-preview"
  deployment_name: "your-deployment-name"

ollama:
  host: "http://localhost:11434"
  model: "deepseek-coder:8b"

rate_limit_defaults:
  max_requests: 10
  time_window: 3600

allowed_users:
  - email: "user1@example.com"
    rate_limit:
      max_requests: 10
      time_window: 3600
  - email: "user2@example.com"
    rate_limit:
      max_requests: 20
      time_window: 3600

app_settings:
  check_interval: 60  # Email check interval in seconds
  max_attachments: 5

logging:
  level: INFO
```

### tasks.yaml

```yaml
- subject: "Summary"
  base_prompt: "Please summarize the following text:"
  output_format: "text"

- subject: "Translate"
  base_prompt: "Please translate the following text to English:"
  output_format: "text"

- subject: "Analysis"
  base_prompt: "Please analyze the following text:"
  output_format: "pdf"
```

## Usage

### Email Interface

Users can send emails to the configured email address with specific subjects that match the defined tasks. The subject format supports optional API and model specifications:

```
TaskName (api:model)
```

Examples:
- `Summary` - Uses default API and model
- `Translate (openai:gpt-4)` - Uses OpenAI's GPT-4 model
- `Analysis (azure:gpt-40)` - Uses Azure OpenAI's GPT-4 model
- `Analysis (openrouter:anthropic/claude-2)` - Uses OpenRouter with Claude-2 model
- `Analysis (ollama:deepseek-coder:8b)` - Uses local Ollama with DeepSeek Coder model

The application will process the email content and any attachments according to the task definition and respond with either text or PDF output.

### Command Line Interface

The application now supports direct task testing through the command line interface. This allows you to test tasks without sending emails.

Available commands:

```bash
# List all available tasks
python main.py --list-tasks

# Process a task with direct input text (using task name)
python main.py --task "Shrnuti" --input "Text k zpracování..."

# Process a task using email-style subject format
python main.py --subject "Shrnuti (openai:gpt-4)" --input "Text k zpracování..."

# Process a task with input from a file
python main.py --task "Preklad" --file "input.txt"

# Specify API and model (when using --task)
python main.py --task "Analyza" --file "input.txt" --api "openai" --model "gpt-4"

# Read input from stdin
echo "Text k překladu" | python main.py --task "Preklad"
```

Command line arguments:
- `--task`, `-t`: Name of the task to execute (do not use with --subject)
- `--subject`, `-s`: Task in email subject format, e.g. "Shrnuti (openai:gpt-4)" or "Analyza (ollama:deepseek-coder)"
- `--input`, `-i`: Direct input text for processing
- `--file`, `-f`: Path to input file
- `--api`: API to use (openai, openrouter, azure, ollama) - ignored when using --subject
- `--model`: Model to use with the specified API - ignored when using --subject
- `--list-tasks`, `-l`: List all available tasks

Examples:
```bash
# Use Ollama with --task parameter
python main.py --task "Shrnuti" --api "ollama" --model "deepseek-coder" --input "Text k zpracování..."

# Use Ollama with --subject parameter
python main.py --subject "Shrnuti (ollama:deepseek-coder)" --input "Text k zpracování..."
```

Note: You can specify the task either using --task with optional --api and --model parameters, or using --subject with email-style format that includes API and model in parentheses. Do not use both --task and --subject together.

The output will be printed to stdout for text format tasks, or saved to 'vysledek.pdf' for PDF format tasks.

## Attachment Support

- Maximum attachment size: 5MB
- Maximum number of attachments: 5 (configurable)
- Supported file types: .txt, .md, .csv, .json, .pdf, .docx

## Rate Limiting

The application includes a rate limiting system that can be configured per user. Default limits can be set in the configuration, and individual users can have custom limits.

## Local AI with Ollama

The application supports local AI inference using Ollama. To use this feature:

1. Install Ollama from https://ollama.ai/
2. Pull the default model:
```bash
ollama pull deepseek-coder:8b
```
3. Configure the Ollama host and default model in config.yaml
4. Use the `ollama:model-name` syntax in email subjects to specify Ollama models

## Security

- Only allowed users (configured in config.yaml) can use the service
- Email authentication required
- Rate limiting prevents abuse
- Attachment size and type restrictions

## Docker Volume Mapping

When running the Docker container, you must map the config directory to provide your configuration files:

```bash
docker run -d \
  -v /path/to/your/config:/app/config \
  --name taskmailerai \
  xnovakm4/taskmailerai
```

Make sure your config directory contains both `config.yaml` and `tasks.yaml` files with appropriate permissions.
