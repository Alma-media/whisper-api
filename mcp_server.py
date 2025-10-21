#!/usr/bin/env python3
"""
MCP Server for Whisper API

This module provides MCP (Model Context Protocol) server functionality for the Whisper transcription service.
It exposes audio transcription capabilities as MCP tools that can be used by MCP-compatible clients.
"""

import asyncio
import base64
import os
import tempfile
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

# Import Whisper functionality
import whisper

# Configuration from environment variables
MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")  # tiny, base, small, medium, large-v3
DEVICE = os.getenv("WHISPER_DEVICE", "cuda" if os.getenv("CUDA", "0") == "1" else "cpu")
ROOT = os.getenv("WHISPER_DOWNLOAD_FOLDER")

# Load Whisper model with error handling
print(f"Loading Whisper model: {MODEL_SIZE} on {DEVICE}", file=__import__('sys').stderr)
try:
    model = whisper.load_model(
        MODEL_SIZE,
        device=DEVICE,
        download_root=ROOT,
    )
    print(f"Model loaded successfully: {MODEL_SIZE}", file=__import__('sys').stderr)
except Exception as e:
    print(f"Error loading model: {e}", file=__import__('sys').stderr)
    raise

# MCP Server instance
server = Server("whisper-transcription")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available transcription tools."""
    tools = [
        Tool(
            name="transcribe_audio",
            description="Transcribe audio file to text using Whisper. Accepts base64-encoded audio data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_data": {
                        "type": "string",
                        "description": "Base64-encoded audio file data (supports wav, mp3, mp4, m4a, flac, etc.)"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename (optional, used for format detection)",
                        "default": "audio.wav"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code for transcription (optional, auto-detect if not specified)",
                        "pattern": "^[a-z]{2}$"
                    },
                    "task": {
                        "type": "string",
                        "description": "Task type: 'transcribe' or 'translate' (default: transcribe)",
                        "enum": ["transcribe", "translate"],
                        "default": "transcribe"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for sampling (0.0 to 1.0, default: 0.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.0
                    },
                    "best_of": {
                        "type": "integer",
                        "description": "Number of candidates when sampling with non-zero temperature (default: 5)",
                        "minimum": 1,
                        "maximum": 25,
                        "default": 5
                    },
                    "beam_size": {
                        "type": "integer",
                        "description": "Number of beams in beam search (default: 5)",
                        "minimum": 1,
                        "maximum": 25,
                        "default": 5
                    }
                },
                "required": ["audio_data"]
            }
        ),
        Tool(
            name="get_model_info",
            description="Get information about the loaded Whisper model and configuration.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_supported_languages",
            description="List all languages supported by Whisper for transcription.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]
    
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "transcribe_audio":
        return await _handle_transcribe_audio(arguments)
    elif name == "get_model_info":
        return await _handle_get_model_info(arguments)
    elif name == "list_supported_languages":
        return await _handle_list_supported_languages(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _handle_transcribe_audio(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle audio transcription."""
    try:
        audio_data = arguments.get("audio_data", "").strip()
        filename = arguments.get("filename", "audio.wav")
        language = arguments.get("language")
        task = arguments.get("task", "transcribe")
        temperature = arguments.get("temperature", 0.0)
        best_of = arguments.get("best_of", 5)
        beam_size = arguments.get("beam_size", 5)
        
        if not audio_data:
            raise ValueError("Audio data cannot be empty")
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 audio data: {str(e)}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or '.wav') as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Prepare transcription options
            options = {
                "task": task,
                "temperature": temperature,
                "best_of": best_of,
                "beam_size": beam_size,
            }
            
            if language:
                options["language"] = language
            
            # Transcribe audio
            result = model.transcribe(temp_file_path, **options)
            
            # Extract transcription details
            text = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")
            
            # Build response
            response_parts = [
                f"**Transcription Result:**",
                f"**Text:** {text}",
                f"**Detected Language:** {detected_language}",
                f"**Task:** {task}",
                f"**Model:** {MODEL_SIZE}",
                f"**Device:** {DEVICE}"
            ]
            
            # Add segments if available
            segments = result.get("segments", [])
            if segments and len(segments) > 1:
                response_parts.append(f"**Segments:** {len(segments)} segments detected")
                response_parts.append("**Detailed Segments:**")
                for i, segment in enumerate(segments[:5]):  # Show first 5 segments
                    start = segment.get("start", 0)
                    end = segment.get("end", 0)
                    segment_text = segment.get("text", "").strip()
                    response_parts.append(f"  {i+1}. [{start:.1f}s - {end:.1f}s]: {segment_text}")
                
                if len(segments) > 5:
                    response_parts.append(f"  ... and {len(segments) - 5} more segments")
            
            return [
                TextContent(
                    type="text",
                    text="\n".join(response_parts)
                )
            ]
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Error during audio transcription: {str(e)}"
            )
        ]


async def _handle_get_model_info(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle getting model information."""
    try:
        # Get model information
        info_parts = [
            f"**Whisper Model Information:**",
            f"**Model Size:** {MODEL_SIZE}",
            f"**Device:** {DEVICE}",
            f"**Download Root:** {ROOT or 'Default (~/.cache/whisper)'}",
        ]
        
        # Add model-specific details
        if hasattr(model, 'dims'):
            dims = model.dims
            info_parts.extend([
                f"**Model Dimensions:**",
                f"  - Audio Features: {dims.n_mels}",
                f"  - Text Tokens: {dims.n_vocab}",
                f"  - Audio Context: {dims.n_audio_ctx}",
                f"  - Text Context: {dims.n_text_ctx}",
                f"  - Audio Layers: {dims.n_audio_layer}",
                f"  - Text Layers: {dims.n_text_layer}",
                f"  - Audio Heads: {dims.n_audio_head}",
                f"  - Text Heads: {dims.n_text_head}",
            ])
        
        # Add supported tasks
        info_parts.extend([
            f"**Supported Tasks:** transcribe, translate",
            f"**Supported Formats:** wav, mp3, mp4, m4a, flac, and more",
        ])
        
        return [
            TextContent(
                type="text",
                text="\n".join(info_parts)
            )
        ]
        
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Error getting model info: {str(e)}"
            )
        ]


async def _handle_list_supported_languages(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle listing supported languages."""
    try:
        # Get Whisper's supported languages
        languages = whisper.tokenizer.LANGUAGES
        
        # Format language list
        language_list = []
        for code, name in sorted(languages.items()):
            language_list.append(f"  - **{code}**: {name}")
        
        response_parts = [
            f"**Whisper Supported Languages ({len(languages)} total):**",
            "",
            *language_list,
            "",
            "**Usage:** Specify the language code (e.g., 'en', 'es', 'fr') in the transcribe_audio tool.",
            "**Auto-detection:** Leave language empty for automatic language detection."
        ]
        
        return [
            TextContent(
                type="text",
                text="\n".join(response_parts)
            )
        ]
        
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Error listing supported languages: {str(e)}"
            )
        ]


async def main():
    """Main entry point for the MCP server."""
    # Initialize the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="whisper-transcription",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
