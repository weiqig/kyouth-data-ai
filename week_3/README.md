# Week 3: System Integration & Application — Resume Helper Chatbot

## Project Overview

This project containerizes a full-stack AI-powered resume helper chatbot, integrating a frontend and backend service with a Gemini (or Ollama) language model. The goal is to allow users to upload their resume as a PDF and receive tailored feedback — such as skill gap analysis, resume critiques, and also general inquiries — through a conversational chat interface.

The application is built as a microservices architecture: a static frontend served using FastAPI, and a Python backend that handles AI model communication. Both services are containerized with Docker and orchestrated using Docker Compose.

---

## Setup Instructions

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v24+ recommended)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+ recommended)
- A Google Gemini API key (required for the default Gemini model)
- Ollama for running local LLMs (This is optional)

### Environment Variables

Copy the provided `.env.example` file to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit the `.env`:

```env
DEFAULT_MODEL=whichever model you want to use that is available
GOOGLE_API_KEY=your_api_key_here
```

> **Never commit your `.env` file.** It is listed in `.gitignore` by default.


## Usage

### Running with Docker Compose

**Default (Gemini model only):**

```bash
docker compose up --build
```

- Builds and starts the frontend and backend services.
- Uses the `DEFAULT_MODEL` specified in your `.env`.

**With Ollama (bonus):**

```bash
docker compose --profile ollama up --build
```

An ollama-initializer container will start automatically to pull the models listed in the .env file and stop once it is done.

- Access the chatbot through: [http://localhost:8000/chat](http://localhost:8000/chat)

**Stopping the services:**

```bash
docker compose down
```


### Expected Response

Users are able to send messages through the chat interface and optionally attach a PDF resume (or images if the model supports multimodal functionality).

**Example:**

```
Resume Helper: "Hello! How can I help you today?"

User: "find skill gaps" (with PDF attached)
Bot: "Here’s a breakdown of the skill gaps, categorized:

Cloud Technologies: AWS, Alibaba Cloud, Google Cloud
Data & Analytics: Datastudio, Power BI, Tableau, Grafana, Data Processing, SQL, Prometheus
Machine Learning: LLM, PyTorch, TensorFlow, Scikit-Learn, Feature Engineering, RAG
DevOps & Infrastructure: CI/CD, Github Actions, Nginx, Linux Development Environments
Programming Languages & Frameworks: Node.js, PHP, Spring Boot, Spring Framework, MySQL, MongoDB
API & Integration: API Integration, Restful API Design
Testing & Code Quality: A/B Testing, Code Reviews, Testing
Web Automation: Web Automation

Do you need further assistance refining your resume based on these skill gaps?"
```

---

## API / Function Reference

### Backend — `POST /chat`

The core endpoint for all chatbot interactions.

**URL -** http://backend:8001/chat  
**Method -** POST  
**Content-Type -** application/json

**Request payload:**

```json
{
  "message": "Can you identify skill gaps in my resume?",
  "pdf_text": "John Doe\nSoftware Engineer\nSkills: Python, React, SQL...",
  "fileType": "pdf"
}
```

| Field      | Type   | Required | Description                                      |
|------------|--------|----------|--------------------------------------------------|
| `message`  | string | Yes      | The user's chat message                          |
| `pdf_text` | string | No       | Extracted plain text from the uploaded PDF       |
| `fileType` | string | No       | File extension type of the uploaded file         |

**Response:**

```json
{
  "response": "Here’s a breakdown of the skill gaps..."
}
```

| Field      | Type   | Description                        |
|------------|--------|------------------------------------|
| `response` | string | The AI-generated chatbot reply     |

---

### Frontend — Key JavaScript Functions

| Function           | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `sendMessage()`    | Reads the user's input and any uploaded PDF, then sends a `POST /chat` request to the backend. Appends the user message and bot response to the chat history. |
| `extractPdfText()` | Uses a PDF parsing library to extract raw text from the uploaded PDF file before sending it to the backend. |
| `renderMessage()`  | Creates and appends a new chat bubble element (user or bot) to the chat history DOM. |

### Docker Network Communication

Within the Docker Compose network, FastAPI proxies API requests to the backend service by its service name. For example:

```
Frontend (browser) → POST http://localhost:8000/chat
  → FastAPI reverse proxy → http://backend:8001/chat
  → Python backend → Gemini API / Ollama
```

This means the frontend JavaScript always targets `localhost:8000`, and FastAPI internally routes `/chat` requests to the backend container — the two services never need to expose internal ports directly to each other.

---

## Data / Assumptions

### Data Flow

1. The user types a message and optionally uploads a PDF in the browser.
2. The frontend extracts text from the PDF (client-side) and sends a JSON payload to `POST /chat`.
3. The backend receives the message and PDF text, constructs a prompt, and calls the configured AI model (Gemini or Ollama).
4. The model's response is returned as JSON to the frontend.
5. The frontend appends the response to the chat interface.

### Message Structure

All communication between frontend and backend uses JSON:

```json
{
  "message": "<user text>",
  "pdf_text": "<extracted resume text or empty string>"
}
```

### Assumptions

- **AI model:** The Gemini model from Week 2 is integrated directly via API call, and acting as a chatbot with access to week_2 functions.
- **PDF input:** The PDF is parsed client-side into plain text before being sent. Only text-based (not scanned/image) PDFs are supported reliably.
- **PDF size:** Large PDFs may produce very long prompts. No explicit size limit is enforced, but excessively long inputs may hit model token limits or cause slower responses.
- **Message length:** No hard limit is enforced on user messages, but very long inputs may be truncated by the model's context window.
- **Stateless sessions:** The backend does not maintain conversation history between requests. Each `/chat` call is independent.

---

## Testing

### Backend Tests — using `curl`

**Basic message (no PDF):**

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "pdf_text": ""}'
```

Expected: `{"response": "Hello! I can analyze your resume if you provide the PDF."}`

**With resume text:**

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my skill gaps?", "pdf_text": "Skills: Python, SQL, React"}'
```

Expected: A skill gap analysis response referencing the provided skills.

**Empty message (edge case):**

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "", "pdf_text": ""}'
```

Expected: A graceful error or prompt asking the user for input.

### Frontend Tests — Manual

| Test Case                        | Steps                                                                 | Expected Result                              |
|----------------------------------|-----------------------------------------------------------------------|----------------------------------------------|
| Send a text message              | Type a message and press Send                                         | Message appears in chat; bot replies         |
| Upload a PDF and ask a question  | Attach a PDF, type "find skill gaps", press Send                      | Bot responds with resume-specific analysis   |
| Upload a text file               | Attempt to attach a `.txt` file                                       | File rejected or ignored gracefully          |
| Upload a png file                | Attempt to attach a `.png` file                                       | Bot responds if multimodal, else replies     |
| Empty message submission         | Press Send without typing anything                                    | No request sent, or user is prompted         |
| Large PDF upload                 | Upload a multi-page PDF (10+ pages)                                   | Response still returned, possibly slower     |

### Verifying Docker Network Communication

To confirm the frontend and backend are communicating correctly inside Docker:

```bash
# Check backend logs for incoming requests
docker compose logs backend

# Exec into the frontend container and curl the backend by service name
docker exec -it <frontend_container_name> sh
curl -X POST http://backend:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "pdf_text": ""}'
```

A successful response confirms the inter-service network is working as expected.



### Regarding GPU over CPU usage for ollama

linux:

```sh
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

issues with sudo systemctl restart docker":

```sh
sudo snap restart docker
```


---

## Limitations

- **No persistent storage for chat history:** Each message is processed independently without any connection between them throughout the session, and chat history is lost when the page is refreshed or the session ends.
- **No user authentication:** The application is open to anyone who can access the URL. Not suitable for production or multi-user deployment without added auth.
- **Single-model inference:** The backend targets one model at a time; there is no fallback if the primary model fails.
- **Gemini API dependency:** The default setup requires an active internet connection and a valid Google API key. Rate limits or API outages will break the chatbot.
- **Token/context limits:** Very long resumes or conversations may exceed the model's context window, causing truncated or degraded responses.
- **Ollama model download:** Pulling Ollama models requires significant disk space (several GB) and a separate manual step after container startup.
- **AI accuracy:** The model may drift leading to inaccurate skill gaps or produce generic advice not tailored to specific industries, hence responses should be treated as suggestions when given context.

---

## Architecture Reflection

### Design Choices

The application uses a **microservices architecture** with a clear separation between the frontend and backend. The frontend handles user interaction and file parsing; the backend is solely responsible for AI model communication. This separation keeps each service focused, independently testable, and replaceable — for example, the backend model could be swapped from Gemini to any other LLM without touching the frontend code.

**Docker and Docker Compose** were chosen to ensure reproducibility across machines. Containerization eliminates "works on my machine" issues and makes the setup a single command for any user with Docker installed. The Docker Compose network also allows services to reference each other by name (`backend`, `ollama`) rather than hardcoded IPs, simplifying configuration.

### Trade-offs

- **Simplicity over features:** The chat interface is intentionally minimal — no authentication, no database, no websocket streaming. This made the system easy to build and debug within a week, at the cost of production-readiness.
- **Ease of deployment over performance:** Docker Compose is simple to run locally but not designed for scaling. A production system would use Kubernetes or a managed container service.
- **Client-side PDF parsing over server-side:** Parsing PDFs in the browser avoids sending raw binary files over the network, but limits support to text-based PDFs and relies on browser compatibility.
- **Gemini by default, Ollama as opt-in:** Using Gemini as the default keeps setup fast and avoids large local downloads, while the `local` profile gives users the option of a fully offline experience.

### Improvements

Given more time, the following extensions would significantly improve the system:

- **Persistent chat history:** Integrate a lightweight database (e.g. SQLite or PostgreSQL) to store and retrieve conversation history across sessions.
- **Multi-model inference:** Implement a retry/fallback mechanism so the system gracefully degrades if the primary model API is unavailable.
- **Server-side PDF processing:** Move PDF parsing to the backend for more robust handling of complex, multi-column, or partially scanned documents.
- **Richer frontend framework:** Replace the basic frontend with React or Vue and implementing bootstrap framework for easier state management and component reuse.
- **User authentication:** Add basic login/session management so multiple users can maintain separate chat histories.

