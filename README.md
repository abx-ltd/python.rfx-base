# RFX Base Platform

A comprehensive backend platform built on domain-driven design (DDD) and CQRS patterns for RFX JSC projects. This repository contains the foundational modules that power modern enterprise applications with strong separation of concerns, event-driven architecture, and scalable domain modeling.

## 🏗️ Architecture Overview

RFX Base is built on the **Fluvius** framework and follows Domain-Driven Design principles with CQRS (Command Query Responsibility Segregation) pattern. Each module represents a bounded context with its own:

- **Domain**: Core business logic and rules
- **Aggregate**: Domain entities and business operations  
- **Command**: Write operations and business actions
- **Query**: Read operations and data projections
- **State Management**: Domain state persistence
- **Model**: Data schemas and database mappings

## 📦 Core Modules

### 🔐 Identity & Access Management
- **`rfx_idm`** - Identity management (not individual user accounts)
- **`rfx_user`** - User profile management, avatars, billing, personal info

### 💬 Communication & Messaging  
- **`rfx_message`** - Message services, templates, and communication workflows
- **`rfx_discussion`** - Discussion threads, tickets, comments, and collaboration tools

### 📊 Project & Client Management
- **`rfx_client`** - Client project management, work packages, milestones, deliverables
- **`rfx_media`** - Media asset management and file handling

### 🏛️ Core Infrastructure
- **`rfx_base`** - Base classes and shared utilities
- **`rfx_cqrs`** - CQRS pattern implementation and domain abstractions
- **`rfx_form`** - Dynamic form generation and data collection
- **`rfx_billing`** - Billing and payment processing (placeholder)

## 🔧 Technology Stack

### Core Framework
- **Fluvius** - Custom domain-driven framework (located in `lib/fluvius/`)
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and Object-Relational Mapping

### Web & API
- **FastAPI** (≥0.115.12) - High-performance async API framework
- **Uvicorn** (≥0.34.2) - ASGI server implementation
- **Gunicorn** (≥23.0.0) - Production WSGI server
- **Starlette** (≥0.46.2) - Lightweight ASGI framework

### Data & Persistence
- **SQLAlchemy** (2.0.37) - Modern SQL toolkit and ORM
- **AsyncPG** (0.30.0) - High-performance PostgreSQL adapter
- **Pypika** (≥0.48.9) - SQL query builder

### Authentication & Security
- **AuthLib** (≥1.5.2) - OAuth and authentication library
- **Sanic-JWT** (1.8.0) - JWT authentication for Sanic
- **Sanic-Security** (1.16.8) - Security utilities
- **ITSDangerous** (≥2.2.0) - Cryptographic signing

### Data Processing & Validation
- **Pydantic** (≥2.11.4) - Data validation using Python type hints
- **PyRsistent** (0.20.0) - Persistent/immutable data structures

### Background Processing
- **ARQ** (0.26.3) - Fast job queueing and RPC in Python
- **GMQTT** - MQTT client for IoT and real-time messaging

### Development & Utilities
- **Ruff** (0.9.1) - Fast Python linter and formatter
- **ULID-PY** (1.1.0) - Universally Unique Lexicographically Sortable Identifier
- **Click** (8.1.8) - Command line interface creation toolkit
- **Whenever** (0.7.3) - Date/time utilities

## 🚀 Getting Started

### Prerequisites
- Python ≥ 3.13
- PostgreSQL database
- Redis (for background tasks)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rfx-base
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements.dev.txt  # For development
   ```

3. **Environment setup**:
   ```bash
   cp app.env.example app.env
   # Edit app.env with your configuration
   ```

4. **Initialize the database**:
   ```bash
   just init-db
   ```

### Running the Application

#### Development Mode
```bash
just run-local
# Runs on http://0.0.0.0:8000 with auto-reload
```

#### Production Mode
```bash
just run-gunicorn
# Runs with Gunicorn WSGI server
```

## 📁 Project Structure

```
rfx-base/
├── src/                    # Source code modules
│   ├── app_main/          # Application entry point
│   ├── rfx_base/          # Base module foundations
│   ├── rfx_idm/           # Identity management
│   ├── rfx_user/          # User profile management
│   ├── rfx_message/       # Messaging & communication
│   ├── rfx_discussion/    # Discussion & collaboration
│   ├── rfx_client/        # Client & project management
│   ├── rfx_media/         # Media asset management
│   ├── rfx_cqrs/          # CQRS implementation
│   ├── rfx_form/          # Dynamic forms
│   └── rfx_billing/       # Billing services
├── biz/                   # Business process repositories
│   └── rfx_01_sample_business/
│       ├── data/          # Data element specifications
│       ├── form/          # Form & data package specs
│       ├── flow/          # Workflow definitions
│       └── rule/          # Business rule definitions
├── lib/
│   └── fluvius/           # Core framework library
├── mig/                   # Database migrations
├── tests/                 # Test suites
├── Justfile              # Task runner commands
└── pyproject.toml        # Project configuration
```

## 🏛️ Domain Architecture

Each RFX module follows a consistent domain-driven structure:

```python
# Example: rfx_user module
from rfx_user import (
    UserProfileDomain,        # Core domain logic
    UserProfileQueryManager,  # Read operations
    UserProfileAggregate,     # Domain entities
    command,                  # Write operations
    model,                    # Data schemas
    policy,                   # Business rules
    provider                  # External integrations
)
```

### Domain Patterns

- **Commands**: Handle business operations and state changes
- **Queries**: Provide read-only data access and projections  
- **Aggregates**: Encapsulate business logic and maintain consistency
- **Policies**: Enforce business rules and constraints
- **State Managers**: Handle domain state persistence
- **Providers**: Integrate with external systems

## 🔌 Available Commands (Just)

The project uses [Just](https://github.com/casey/just) as a command runner:

```bash
just --list                 # Show all available commands
just run-local              # Start development server
just run-gunicorn           # Start production server
just init-db                # Initialize database
just echo-config            # Display configuration
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific module tests
python -m pytest tests/rfx_user/
python -m pytest tests/rfx_message/
```

## 📚 Business Process Management

The `biz/` directory contains business process definitions:

- **Data Specifications**: Reusable data element definitions
- **Form Specifications**: Dynamic form and data package layouts
- **Workflow Definitions**: Business process flows and rules
- **Rule Definitions**: Business logic and validation rules

## 🔧 Configuration

Configuration is managed through:
- `app.env` - Environment-specific settings
- `pyproject.toml` - Project metadata and dependencies
- Module-specific `_meta/defaults.py` files

## 🤝 Contributing

1. Follow the domain-driven design patterns established in existing modules
2. Ensure all new features include appropriate tests
3. Use the established module structure for consistency
4. Run linting with `ruff` before submitting changes

## 📄 License

[Add your license information here]

---

**RFX Base Platform** - Empowering enterprise applications with modern, scalable, domain-driven architecture.