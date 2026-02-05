---
name: hello-world
version: 1.0.0
description: A simple example agent that demonstrates the RappterHub agent format
author: rappterhub
license: MIT
runtime: python
tags:
  - example
  - starter
  - hello-world
requires:
  python: ">=3.10"
---

## Overview

This is a simple example agent that demonstrates the basic structure of a RappterHub agent. Use it as a template for creating your own agents.

## Usage

```python
# The agent will respond to greetings
result = agent.execute(query="hello")
# Returns: {"status": "success", "message": "Hello! I'm a RappterHub agent.", ...}

# It can also tell you about itself
result = agent.execute(query="what can you do?")
```

## Features

- Responds to greetings
- Provides information about itself
- Demonstrates the standard agent response format

## Configuration

No configuration required. This agent works out of the box.
