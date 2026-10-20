<h1 align="center">UfaFlow</h1>

<p align="center">
  Lightweight async worker manager and load balancer for Python services.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.5-7c3aed?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge" alt="license" />
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/Release-1.0.5-10b981?style=for-the-badge" alt="release" />
  <img src="https://img.shields.io/badge/FastAPI-✓-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="fastapi" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/SQLite-✓-6b7280?style=for-the-badge&logo=sqlite&logoColor=white" alt="sqlite" />
  <img src="https://img.shields.io/badge/AIO-Default-4f46e5?style=for-the-badge" alt="aio default" />
  <img src="https://img.shields.io/badge/PostgreSQL-✓-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="postgresql" />
  <img src="https://img.shields.io/badge/Clustered%20GUI-✓-2563eb?style=for-the-badge" alt="clustered gui" />
</p>

<p align="center">
  <a href="https://github.com/your-org/ufaflow/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/your-org/ufaflow/ci.yml?branch=main&label=CI&style=flat-square" alt="CI status" />
  </a>
  <img src="https://img.shields.io/badge/npm-0%20vulns-2E7D32?style=flat-square" alt="npm audit" />
  <img src="https://img.shields.io/badge/security-audits-passing-16a34a?style=flat-square" alt="security audits" />
  <img src="https://img.shields.io/badge/docs-latest-0ea5e9?style=flat-square" alt="docs" />
  <img src="https://img.shields.io/badge/status-stable-22c55e?style=flat-square" alt="status" />
  <img src="https://img.shields.io/github/stars/your-org/ufaflow?style=flat-square&logo=github&label=stars" alt="stars" />
  <img src="https://img.shields.io/github/issues/your-org/ufaflow?style=flat-square&logo=github&label=issues" alt="issues" />
  <img src="https://img.shields.io/github/last-commit/your-org/ufaflow?style=flat-square&logo=github&label=last%20commit" alt="last commit" />
</p>

## Overview

UfaFlow is a lightweight asynchronous worker manager and load balancer designed for Python services. It helps distribute traffic across worker processes, manage runtime lifecycle, and provide a predictable execution model for production-ready workloads.

## Features

- Async-first worker orchestration
- Configurable process pool and worker allocation
- Lightweight load balancing across workers
- Support for FastAPI and Python service integration
- Config-driven runtime setup
- Built for clean local development and release validation

## Quick Start

```bash
pip install ufaflow