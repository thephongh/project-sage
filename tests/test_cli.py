"""Test CLI functionality."""

import pytest
from typer.testing import CliRunner
from sage.cli import app


def test_version_command():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    
    assert result.exit_code == 0
    assert "Project Sage" in result.stdout


def test_status_command_not_initialized():
    """Test status command when project is not initialized."""
    runner = CliRunner()
    result = runner.invoke(app, ["status"])
    
    assert result.exit_code == 1
    assert "not initialized" in result.stdout


def test_ask_command_not_initialized():
    """Test ask command when project is not initialized."""
    runner = CliRunner()
    result = runner.invoke(app, ["ask", "test question"])
    
    assert result.exit_code == 1
    assert "not initialized" in result.stdout


def test_update_command_not_initialized():
    """Test update command when project is not initialized."""
    runner = CliRunner()
    result = runner.invoke(app, ["update"])
    
    assert result.exit_code == 1
    assert "not initialized" in result.stdout