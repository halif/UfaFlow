<h1 align="center">UfaFlow</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.5-7c3aed?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge" alt="license" />
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

UfaFlow is a lightweight asynchronous worker manager and load balancer for Python services. It is designed to distribute requests across worker processes with predictable lifecycle management, process supervision, and a minimal operational footprint.

The project focuses on:
- clean process orchestration
- stable runtime behavior
- simple deployment patterns
- predictable startup and shutdown semantics

## Why UfaFlow

Many service workloads require more than a single process but less than a full operational platform. UfaFlow provides a small, controllable runtime layer for:
- worker-based request handling
- simple cluster orchestration
- async execution with process isolation
- operational transparency for lightweight deployments

## Key Features

- Async-first worker orchestration
- Configurable worker pool and process management
- Lightweight request balancing across workers
- FastAPI-ready execution model
- YAML-based configuration support
- Clean startup and shutdown lifecycle controls

## Quick Start

### Installation

```bash
pip install ufaflow