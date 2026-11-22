# Applied Lab R40-T005: Client-Configuration Validation & Offline Service Adapter

## Overview

This lab extends [Lesson 14: The Generative AI Application Lifecycle](../../README.md) by implementing strict client-side configuration validation and a deterministic offline service adapter for model server deployment.

Operationalizing generative AI models requires robust configuration schemas. Server startup crashes often occur due to formatting errors (such as passing arguments as a single string instead of an array). In addition, security compliance requires audit summaries to redact runtime environment secrets.

## Validation Contract & Error Rules

1. **Required Command**: Must be a non-empty string. Missing or blank command raises `ConfigurationValidationError`.
2. **Argument Array Contract**: Arguments must be passed as an array/list of strings. Passing arguments as a single string raises `ConfigurationValidationError`.
3. **Environment Redaction**: All environment variable values are replaced with `[REDACTED]` in the output summary.
4. **Execution Safety**: The service adapter validates and prepares the launch summary without spawning any OS subprocess.

## Focus: Offline Adapter & Unestablished Behaviors

The server execution dependency is isolated behind a callable interface (`OfflineServiceAdapter`).
While this adapter guarantees structural correctness and schema validity locally, it explicitly documents real-service behaviors that cannot be verified without real cloud/hardware infrastructure:
- Port availability and socket bind collisions (`EADDRINUSE`)
- Host binary execution permissions and PATH resolution
- Hardware GPU memory limits (VRAM / CUDA OOM)
- Remote network latency, TLS negotiation, and service health

## Invocations & Scenarios

Run the scenarios from repository root:

```bash
# Valid configuration -> redacted summary without process spawn
python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t005/example.py --scenario normal

# Missing command failure
python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t005/example.py --scenario missing_cmd

# Single string arguments failure
python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t005/example.py --scenario string_args

# Canonical check
python3 14-the-generative-ai-application-lifecycle/applied-labs/r40-t005/example.py --check

# Automated unit tests
python3 -m unittest discover -s 14-the-generative-ai-application-lifecycle/applied-labs/r40-t005 -p "test_*.py" -v
```
