#!/usr/bin/env python3
"""
Standalone MCP server runner for Whisper API.

This script runs the Whisper transcription service as an MCP server.
Usage: python run_mcp_server.py
"""

import asyncio
import sys
from mcp_server import main

if __name__ == "__main__":
    print("Starting Whisper Transcription MCP Server...", file=sys.stderr)
    asyncio.run(main())
