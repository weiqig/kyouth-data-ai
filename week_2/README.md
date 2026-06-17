# Week 2 : AI Component

# Project Overview

This project focuses on building a hybrid skill extraction and feature engineering pipeline using both:

- Regex-based extraction
- LLM-assisted extraction

## Regex-Based Skill Extraction

Fast and lightweight extraction using predefined regex patterns for:

- Languages
- Frameworks
- Databases
- Cloud tooling
- AI/ML technologies
- DevOps tooling

This method allows us to extract the skills without consuming any tokens to save on token costs.

## LLM-Assisted Extraction

Fallback extraction using local LLMs through Ollama for cases where regex extraction fails or descriptions require contextual inference.

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

# Project Setup & Installation Instructions

Project structure used according to the Notion page:

```
week_2/
├── data/
├── sql/
├── .env.example         # .env template file
├── .gitignore
├── .python-version      # added for consistency
├── prompt_model.py
├── find_skill_gaps.py
├── rate_limits.txt
├── pyproject.toml       # Environment & Dependencies (using `uv`)
├── tag_data.py
├── uv.lock
└── README.md
```

## Setting up the uv project and .env file

Setup uv astral:

```
curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.8.0 sh
```

Setup venv and sync dependencies:

```
uv sync
```

Copy over a new .env file for custom configuration:

```
cp .env.example .env
```

Make sure to set up the API key in the .env file!

## Ollama Installation

- Install ollama before pulling the required models using ollama pull <model>.

```bash
curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.21.0 sh
```

Mandatory supported models include:

- llama3.1
- phi3
- deepseek-r1:1.5b

Gemini models can also be applied using the API key created in Google AI Studio, a better choice in cases where running ollama locally becomes a problem due to laptop spec or lack of RAM memory for the local LLMs to produce a response.

## Usage commands

Prompt the LLM model:

```
uv run prompt_model.py <model_name> <prompt>
```

Tag tech stack data in the database:

```
uv run tag_data.py
```

Find skill gaps in resume file:

```
uv run find_skill_gaps.py
```

## API / Function Reference

### prompt_model.py
- Prompt the specified LLM model
- <model_name>: str - the model to use <prompt>: str - the prompt to be sent to the LLM model
- outputs a string containing the response from the LLM model.

### tag_data.py
- Tags the tech stacks based on the job descriptions in each record of the jobs table in the database
- Inputs <databse_url>: str - path to the .db file location to be accessed
- Processes the records in the .db file jobs table; returns None on success / failure

### find_skill_gaps.py
- Filters missing skills from the resume according to the tech stacks in the database
- Inputs <input_file_path>: str - path to the file to be analyzed and processed <db_url>: str - path to the .db file location to be accessed
- Outputs a pydantic class containing the gaps, total time taken by the model to respond, and the tokens used by the model

## Data / Assumptions

The data from the week_1 database and the latest .db and .txt files were used in testing the LLM models responses and capabilities, with the assumptions on how the data is processed (in this case the LLMs are expected to return a json array or csv string depending on the function being performed); it is found that each LLM has a certain limit on how much data can be processed either due to the size of the model or how specific the prompt provided is, as providing an extremely long prompt will more likely cause the model to start explaining everything or drift and hallucinate.

### Rate limit calculation

Batch size was determined based on the rate limit calculations shown below:

```sh
((TPM / RPM) * buffer) / observed tokens used
```

TPM / RPM - Average tokens per request
buffer - buffer to account for deviations and variations in description length and response size
observed tokens used - average tokens used per request based on collected data

The average tokens per request available were computed as TPM/RPM, and a buffer value of 0.8 was applied to reserve 20% of the token budget to account for deviations in job description length, response size, and tokenization overhead. This reduces the likelihood of exceeding TPM limits while maintaining efficient throughput.


# Notes on LLM performance

for the local LLMs running with ollama:

- llama3.1 is capable of performing its tasks with minimal issues due to its size
- phi3 over explains a lot and requires very strict prompts to make it behave
- deepseek a somewhat hit or miss, albeit being able to perform slightly bettwe than phi3

Overall, based on local testing between different devices, it can be infered that the correlation between the size of the llm model and the amount of RAM memory required is directly proportional, whereby more lightweight models require less processing power and vice versa; also noting that lightweight models require more prompting in order to do the same tasks by more bigger LLMs, which is understandable.

# Design Choices & Testing

This section serves to summarize the design choices and limitations and trade-offs of the model decisions made:

model_prompt.py - implemented error handling and handling for gemini models within the default prompt_model function, scalability issues in the case of adding handling for other llms

tag_data.py - introduced rate limit calculations for gemini models and resort to defult configurations when prompting with local LLMs; prompt is rigid and constrained which leads to invalid responses from most ollama models, with gemini models faring better in comparison

find_skill_gaps.py - skill formatting and normalization to filter out duplicates and tech stack formats, with the clear issue of being unable to handle skill sets outside of what is listed in the file itself

### Testing

testing can be summarized in the sense of:

using the same prompts for all models for consistency with the drawbacks of LLM models suffering from drift and lack of context, refer to limitation for a more detailed explaination on the topic of model drifting. Accuracy with the data output across the models used even with 0 temperature, likely due to factors such as context, prompt length, and model size and processing power.


# Limitations

## Model drifting

LLM Models can sometimes hallucinate and not follow the instructions provided, leading to a lot of errors. Additionally, procesing data in large batches will also cause the LLM to start explaining, hence there has ben adjustments to the rate limit calculation to set the batch size to lower numbers in order to minimize drifting, although this may fail occasionally as well.

This generally applies to models used in ollama; gemini llm models performed accordingly without issue.

## Regex matching to minimize LLM token usage
Given the inconsistency of the local LLM models and assistance and inquiry from AI, regex matching was suggested and ultimately implemented to process the data without the use of LLMs unless necessary in order to optimize token usage. However, this does in a sense go against the purpose of implementing AI to analyze and provide and tag the appropriate data although the results were more likely to be more consistent in the long run.


# Future Improvements

- Improved entity normalization
- Skill categorization
- Front-end integration
- Skill gap scoring system
- Automated benchmarking dashboard
