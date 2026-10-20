<h1 align="center">UfaFlow</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.5-7c3aed?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="license" />
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/Release-1.0.5-10b981?style=for-the-badge" alt="release" />
  <img src="https://img.shields.io/badge/FastAPI-✓-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="fastapi" />
</p>

<p align="center">
  <a href="https://github.com/halif/ufaflow/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/halif/ufaflow/ci.yml?branch=main&label=CI&style=flat-square" alt="CI status" />
  </a>
  <img src="https://img.shields.io/badge/security-audits-passing-16a34a?style=flat-square" alt="security audits" />
  <img src="https://img.shields.io/badge/status-stable-22c55e?style=flat-square" alt="status" />
  <img src="https://img.shields.io/github/stars/halif/ufaflow?style=flat-square&logo=github&label=stars" alt="stars" />
  <img src="https://img.shields.io/github/issues/halif/ufaflow?style=flat-square&logo=github&label=issues" alt="issues" />
  <img src="https://img.shields.io/github/last-commit/halif/ufaflow?style=flat-square&logo=github&label=last%20commit" alt="last commit" />
</p>

## Overview

UfaFlow is a lightweight asynchronous worker manager and load balancer for Python services. It is designed to distribute work across worker processes with predictable lifecycle control, simple configuration, and a minimal operational footprint.

The project is built for teams that need:
- a simple worker runtime
- process-level isolation
- async-first execution
- predictable startup and shutdown behavior
- easy deployment in development and production-like environments

## Why UfaFlow

Many applications need more than a single process, but do not require the complexity of a full orchestration platform. UfaFlow acts as a lightweight execution layer that helps you:
- manage multiple workers with a single runtime
- balance traffic or task distribution across processes
- keep lifecycle management explicit and controllable
- reduce operational overhead for small-to-medium service deployments

## Key Features

- Async-first worker orchestration
- Configurable worker pool and process management
- Lightweight request balancing across workers
- Support for FastAPI and Python service integration
- YAML-based configuration
- Clean startup and shutdown lifecycle behavior
- Simple deployment model for local and cloud environments

## Installation

```bash
pip install ufaflow
```

## Licence
MIT