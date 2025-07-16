"""
LangChain tools for Dify workflow integration.

This module contains custom LangChain tools that wrap Dify workflows:
- DifyMonologueTool: Character background monologue generation
- DifyQnATool: Query and answer functionality
"""

from .dify_tools import DifyMonologueTool, DifyQnATool

__all__ = ["DifyMonologueTool", "DifyQnATool"]
