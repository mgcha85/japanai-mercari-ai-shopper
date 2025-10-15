import os
import sys
import pytest
import subprocess


@pytest.mark.skip(reason="Run inside container: docker compose run --rm tests to enable")
def test_cli_help():
    proc = subprocess.run([sys.executable, "-m", "mercari_ai_shopper.run", "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Mercari AI Shopper CLI" in proc.stdout
