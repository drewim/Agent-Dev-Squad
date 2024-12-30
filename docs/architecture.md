# System Architecture

This document describes the overall architecture of the AI Software Development Team project.

## Components

The system is composed of the following main components:

*   **Task Queue (Redis):** A Redis-based queue for storing and managing tasks.
*   **Scheduler:** A component that assigns tasks to agents based on resource availability and dependencies.
*   **Resource Manager:** A component that tracks system resources and agent availability.
*   **Message Pipeline (HTTP):** A simple HTTP-based message pipeline for communication between agents.
*   **AI Agents:** A team of AI agents with different roles and responsibilities.
*   **Code Repository (Git):** A Git repository for storing the project codebase.
*   **External LLM API:** An API gateway for connecting to external LLMs.

## Interactions

The components interact with each other as follows:

1.  The **Architect** creates initial tasks and adds them to the **Task Queue**.
2.  The **Scheduler** reads tasks from the **Task Queue** and assigns them to agents based on resource availability.
3.  **Agents** report their resource usage to the **Resource Manager**.
4.  **Agents** communicate with each other through the **Message Pipeline**.
5.  **Agents** can request assistance from external LLMs via the **API Gateway**.
6.  The **Project Manager** monitors the overall progress of the project.

## Diagram

```mermaid
graph LR
    subgraph "System"
        subgraph "Core Components"
            TaskQueue(Task Queue - Redis)
            Scheduler(Scheduler)
            ResourceManager(Resource Manager)
            MessagePipeline(Message Pipeline - HTTP)
        end

        subgraph "AI Agents"
            Architect(Head Architect)
            ProjectManager(Project Manager)
            SeniorDev(Senior Software Dev)
            JuniorDev1(Junior Dev 1)
            JuniorDev2(Junior Dev 2)
            TestDev(Test Dev Agent)
        end
        
        subgraph "Code Repository"
            GitRepo(Git Repository)
        end

        subgraph "External LLM API"
            APIGateway(API Gateway)
            ExternalLLM(External LLMs - OpenAI/etc)
        end
        
        subgraph "Data Storage"
            DataStorage(Data storage - models/logs etc)
        end
    end

    %% Core Component Interactions
    Scheduler --> TaskQueue: Reads Tasks
    Scheduler --> ResourceManager: Query Resources
    Scheduler --> Architect: Assigns Tasks
    Scheduler --> SeniorDev: Assigns Tasks
    Scheduler --> JuniorDev1: Assigns Tasks
    Scheduler --> JuniorDev2: Assigns Tasks
    Scheduler --> TestDev: Assigns Tasks

    ResourceManager --> Architect: Tracks Resources
    ResourceManager --> SeniorDev: Tracks Resources
    ResourceManager --> JuniorDev1: Tracks Resources
    ResourceManager --> JuniorDev2: Tracks Resources
    ResourceManager --> TestDev: Tracks Resources

    %% Agent Interactions
    Architect --> TaskQueue: Adds/Updates Tasks
    ProjectManager --> TaskQueue: Reads Task Status
    ProjectManager --> ResourceManager: Reads Resource Status
    SeniorDev --> JuniorDev1: Provides Feedback (via MessagePipeline)
    SeniorDev --> JuniorDev2: Provides Feedback (via MessagePipeline)
    SeniorDev --> GitRepo: Updates Code
    JuniorDev1 --> GitRepo: Updates Code
    JuniorDev2 --> GitRepo: Updates Code
    TestDev --> GitRepo: Updates Code

    JuniorDev1 --> SeniorDev: Requests Help (via MessagePipeline)
    JuniorDev2 --> SeniorDev: Requests Help (via MessagePipeline)
    SeniorDev --> APIGateway: External LLM help (if needed)
    JuniorDev1 --> APIGateway: External LLM help (if needed)
    JuniorDev2 --> APIGateway: External LLM help (if needed)
    TestDev --> APIGateway: External LLM help (if needed)
    
    APIGateway --> ExternalLLM: Makes API requests

    %% Message Pipeline Interactions
    MessagePipeline <--> Architect
    MessagePipeline <--> ProjectManager
    MessagePipeline <--> SeniorDev
    MessagePipeline <--> JuniorDev1
    MessagePipeline <--> JuniorDev2
    MessagePipeline <--> TestDev
    
    %% Data storage
    DataStorage <--> GitRepo
    DataStorage <--> Architect
    DataStorage <--> SeniorDev
    DataStorage <--> JuniorDev1
    DataStorage <--> JuniorDev2
    DataStorage <--> TestDev