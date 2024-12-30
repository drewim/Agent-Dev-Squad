# Project Title
 AI Software Development Team

## Developed by:
Drew Imhof <drew.c.imhof@gmail.com>

## Project Description
A team of AI agents to help develop software projects. There is currently an agent to organize the project and break down tasks, the architect, an agent to report on tasks and statuses, the project manager, and software developer agents, including a senior dev, junior devs, and a test dev. These agents can use different models depending on resources available.

Still very much in early development phase.

## Key Features
AI-powered software development using a team of agents.
Local LLM integration with Ollama.
Task queue and scheduler for managing development workflow.
Resource management for efficient task allocation.
Structured responses with confidence levels for better decision-making.

## Technology Stack:
Python
Redis
Ollama
Pydantic
Requests
Psutil
Torch

## Setup Instructions:
Install Pixi: curl -fsSL https://pixi.sh/install.sh | bash
Initialize Pixi: pixi init
Add dependencies to pixi.toml
Install dependencies: pixi install
Start Redis: docker run -p 6379:6379 redis
Start Ollama: ollama serve
Run the project: pixi run python src/main.py