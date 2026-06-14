# Week 2 : AI Component

# Feature Engineering and LLM Integration

## Objective

As input becomes more varied and unpredictable, rule-based systems become harder to manage because they require many specific conditions and cases. Large language models offer a more flexible approach by identifying patterns and generating likely interpretations instead of relying on exact matches.

Using the cleaned data from Week 1, this project builds the AI component of a skill gap detection pipeline responsible for handling the business logic and decision-making of the application. The extracted and engineered features will later be integrated with a front-end application in Week 3.

---

# AI Usage Guidelines

AI can significantly improve developer productivity, especially for repetitive tasks, implementation support, and rapid prototyping. However, AI should be used intentionally and responsibly throughout the development process.

## Guidelines

- Use AI to accelerate repetitive or time-consuming work.
- Understand the problem before prompting AI systems.
- Treat AI-generated output as a starting point, not a final solution.
- Review, validate, and test all generated code and responses.
- Avoid blindly copying or “vibe coding” without understanding the implementation.
- Collaborate with peers and seek feedback regularly.

This project emphasizes problem-solving, reasoning, and system design rather than dependency on AI-generated solutions.

---

# General Instructions

## Development Requirements

- Do not commit artifacts, blobs, test outputs, or secrets to the repository.
- Use a `.gitignore` file where necessary.
- Follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) for all commit messages.
- Format Python code using:
  
```bash
ruff==0.15.*
```

- Required Python version:

```bash
Python 3.14.*
```

- Required package manager version:

```bash
uv==0.8.*
```

- Remove unused dependencies from `pyproject.toml`.
- Pin all package versions exactly to avoid breaking changes.
- Ensure compatibility across:
  - Linux
  - macOS
  - Windows

Platform-dependent implementations will be considered incomplete.

---

# Core Concepts

- LLM Setup and Installation
- Input and Output Serialization
- LLM Resource Management
- LLM Performance Benchmarking
- LLM Feature Engineering

---

# Project Overview

This project focuses on building a hybrid skill extraction and feature engineering pipeline using both:

- Regex-based extraction
- LLM-assisted extraction

The pipeline processes job descriptions stored inside a SQLite database and extracts:

- Programming languages
- Frameworks
- Databases
- Cloud platforms
- APIs
- AI/ML tooling
- Developer tooling
- General software engineering skills

The extracted technologies and skills are normalized and stored back into the database for downstream skill-gap analysis.

---

# Features

## Regex-Based Skill Extraction

Fast and lightweight extraction using predefined regex patterns for:

- Languages
- Frameworks
- Databases
- Cloud tooling
- AI/ML technologies
- DevOps tooling

## LLM-Assisted Extraction

Fallback extraction using local LLMs through Ollama for cases where regex extraction fails or descriptions require contextual inference.

Supported models include:

- llama3.1
- phi3
- qwen2.5-coder
- gemma3
- deepseek-r1:1.5b

## Hybrid Processing Pipeline

Workflow:

```text
Regex Extraction
        ↓
Missing Skills
        ↓
LLM Inference
        ↓
Validation & Serialization
        ↓
Database Update
```

## Output Validation

The system validates:

- JSON formatting
- Missing keys
- Hallucinated IDs
- Batch mismatches
- Invalid response structures

## Performance Benchmarking

Tracks:

- Total token usage
- Total processing duration
- Batch execution statistics
- LLM response timing

---

# Database Structure

## Table: `JOBS`

| Column | Description |
|---|---|
| `source_id` | Original job source ID |
| `job_title` | Job title |
| `company` | Company name |
| `description` | Job description |
| `tech_stack` | Extracted skills and technologies |

---

# Example Output

```json
[
  {
    "id": "91647393",
    "tech_stack": "Python, FastAPI, PostgreSQL, Docker"
  }
]
```

---

# Example Tech Stack Coverage

## Languages

- Python
- JavaScript
- TypeScript
- Java
- C++
- C#
- PHP
- Go

## Frameworks

- React
- Vue
- Angular
- Django
- Flask
- FastAPI
- Spring Boot
- Express.js
- NestJS

## Databases

- PostgreSQL
- MySQL
- SQLite
- MongoDB
- Redis

## Cloud & DevOps

- AWS
- Azure
- GCP
- Docker
- Kubernetes
- Terraform
- Jenkins
- CI/CD

## AI / ML

- OpenAI
- LLM
- LangChain
- RAG
- TensorFlow
- PyTorch
- Scikit-learn

---

# Running the Project

## Install dependencies

```bash
uv sync
```

## Run the extraction pipeline

```bash
python main.py
```

---

# Future Improvements

- Improved entity normalization
- Skill categorization
- Embedding-based semantic matching
- Multi-model ensemble extraction
- Front-end integration
- Skill gap scoring system
- Automated benchmarking dashboard
