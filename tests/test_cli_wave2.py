"""
Tests for Wave 2 CLI enhancements.
"""

import json
import pytest
import yaml
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

# Skip if click is not available
pytest.importorskip("click")

# Import CLI commands
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from cli import (
    cli,
    load_config,
    save_config,
    load_profile,
    save_profile,
    get_env_config,
    merge_configs,
)


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create temporary config directory."""
    config_dir = tmp_path / ".agentmind"
    config_dir.mkdir()

    # Patch CONFIG_DIR and related paths
    import cli

    monkeypatch.setattr(cli, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cli, "CONFIG_FILE", config_dir / "config.yaml")
    monkeypatch.setattr(cli, "PROFILES_FILE", config_dir / "profiles.yaml")

    return config_dir


class TestConfigManagement:
    """Test configuration management functions."""

    def test_save_and_load_config(self, temp_config_dir, monkeypatch):
        """Test saving and loading configuration."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "CONFIG_FILE", temp_config_dir / "config.yaml")

        config = {"provider": "ollama", "model": "llama3.2", "temperature": 0.7}

        save_config(config)
        loaded = load_config()

        assert loaded == config

    def test_save_and_load_profile(self, temp_config_dir, monkeypatch):
        """Test saving and loading profiles."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "PROFILES_FILE", temp_config_dir / "profiles.yaml")

        profile_data = {"provider": "openai", "model": "gpt - 4", "temperature": 0.8}

        save_profile("production", profile_data)
        loaded = load_profile("production")

        assert loaded == profile_data

    def test_get_env_config(self, monkeypatch):
        """Test getting configuration from environment variables."""
        monkeypatch.setenv("AGENTMIND_PROVIDER", "anthropic")
        monkeypatch.setenv("AGENTMIND_MODEL", "claude - 3")
        monkeypatch.setenv("AGENTMIND_TEMPERATURE", "0.9")

        config = get_env_config()

        assert config["provider"] == "anthropic"
        assert config["model"] == "claude - 3"
        assert config["temperature"] == 0.9

    def test_merge_configs(self):
        """Test merging configurations."""
        base = {"provider": "ollama", "model": "llama3.2", "temperature": 0.7}
        override = {"model": "gpt - 4", "temperature": 0.9}

        merged = merge_configs(base, override)

        assert merged["provider"] == "ollama"
        assert merged["model"] == "gpt - 4"
        assert merged["temperature"] == 0.9


class TestInitCommand:
    """Test agentmind init command."""

    def test_init_basic(self, runner, tmp_path, monkeypatch):
        """Test basic project initialization."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            cli,
            [
                "init",
                "--name",
                "test - project",
                "--description",
                "Test project",
                "--provider",
                "ollama",
                "--template",
                "basic",
                "--no - interactive",
            ],
        )

        assert result.exit_code == 0
        assert (tmp_path / "test - project").exists()
        assert (tmp_path / "test - project" / "main.py").exists()
        assert (tmp_path / "test - project" / "requirements.txt").exists()
        assert (tmp_path / "test - project" / "config" / "config.yaml").exists()

    def test_init_with_existing_directory(self, runner, tmp_path, monkeypatch):
        """Test initialization with existing directory."""
        monkeypatch.chdir(tmp_path)
        project_dir = tmp_path / "existing - project"
        project_dir.mkdir()

        result = runner.invoke(
            cli,
            [
                "init",
                "--name",
                "existing - project",
                "--description",
                "Test",
                "--provider",
                "ollama",
                "--template",
                "basic",
                "--no - interactive",
            ],
            input="n\n",
        )

        # Should ask for confirmation and cancel
        assert "exists" in result.output.lower()

    def test_init_creates_correct_structure(self, runner, tmp_path, monkeypatch):
        """Test that init creates correct directory structure."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            cli,
            [
                "init",
                "--name",
                "structured - project",
                "--description",
                "Test",
                "--provider",
                "ollama",
                "--template",
                "research",
                "--no - interactive",
            ],
        )

        project_path = tmp_path / "structured - project"
        assert (project_path / "agents").exists()
        assert (project_path / "config").exists()
        assert (project_path / "tests").exists()
        assert (project_path / "logs").exists()
        assert (project_path / "README.md").exists()


class TestAgentCreateCommand:
    """Test agentmind agent create command."""

    def test_agent_create_basic(self, runner):
        """Test basic agent creation."""
        result = runner.invoke(
            cli,
            ["agent", "create", "--name", "TestAgent", "--role", "Tester", "--no - interactive"],
        )

        assert result.exit_code == 0
        assert "TestAgent" in result.output
        assert "Tester" in result.output

    def test_agent_create_with_output(self, runner, tmp_path):
        """Test agent creation with output file."""
        output_file = tmp_path / "test_agent.py"

        result = runner.invoke(
            cli,
            [
                "agent",
                "create",
                "--name",
                "DataAnalyst",
                "--role",
                "Data Analysis Expert",
                "--output",
                str(output_file),
                "--no - interactive",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "DataAnalyst" in content
        assert "Data Analysis Expert" in content

    def test_agent_create_with_custom_prompt(self, runner):
        """Test agent creation with custom system prompt."""
        result = runner.invoke(
            cli,
            [
                "agent",
                "create",
                "--name",
                "CustomAgent",
                "--role",
                "Custom Role",
                "--system - prompt",
                "Custom system prompt here",
                "--no - interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Custom system prompt here" in result.output


class TestTestCommand:
    """Test agentmind test command."""

    @patch("subprocess.run")
    def test_test_basic(self, mock_run, runner):
        """Test basic test execution."""
        mock_run.return_value = MagicMock(returncode=0)

        result = runner.invoke(cli, ["test"])

        assert result.exit_code == 0
        mock_run.assert_called_once()

        # Check pytest was called
        call_args = mock_run.call_args[0][0]
        assert "pytest" in call_args

    @patch("subprocess.run")
    def test_test_with_coverage(self, mock_run, runner):
        """Test execution with coverage."""
        mock_run.return_value = MagicMock(returncode=0)

        result = runner.invoke(cli, ["test", "--coverage"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--cov=agentmind" in call_args

    @patch("subprocess.run")
    def test_test_with_markers(self, mock_run, runner):
        """Test execution with markers."""
        mock_run.return_value = MagicMock(returncode=0)

        result = runner.invoke(cli, ["test", "--markers", "integration"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "-m" in call_args
        assert "integration" in call_args


class TestDeployCommand:
    """Test agentmind deploy command."""

    def test_deploy_docker_dry_run(self, runner):
        """Test Docker deployment in dry - run mode."""
        result = runner.invoke(cli, ["deploy", "--target", "docker", "--env", "dev", "--dry - run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "docker" in result.output.lower()

    def test_deploy_kubernetes_dry_run(self, runner):
        """Test Kubernetes deployment in dry - run mode."""
        result = runner.invoke(
            cli, ["deploy", "--target", "kubernetes", "--env", "staging", "--dry - run"]
        )

        assert result.exit_code == 0
        assert "kubernetes" in result.output.lower()

    def test_deploy_local(self, runner):
        """Test local deployment."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = runner.invoke(
                cli, ["deploy", "--target", "local", "--env", "dev", "--dry - run"]
            )

            assert result.exit_code == 0


class TestBenchmarkCommand:
    """Test agentmind benchmark command."""

    def test_benchmark_basic(self, runner):
        """Test basic benchmark execution."""
        result = runner.invoke(cli, ["benchmark", "--iterations", "5", "--agents", "2"])

        assert result.exit_code == 0
        assert "Benchmark Results" in result.output
        assert "Iterations" in result.output

    def test_benchmark_with_output(self, runner, tmp_path):
        """Test benchmark with output file."""
        output_file = tmp_path / "benchmark_results.json"

        result = runner.invoke(
            cli, ["benchmark", "--iterations", "3", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "iterations" in data
            assert "runs" in data
            assert len(data["runs"]) == 3


class TestConfigCommands:
    """Test configuration management commands."""

    def test_config_init(self, runner, temp_config_dir, monkeypatch):
        """Test config init command."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "CONFIG_FILE", temp_config_dir / "config.yaml")

        result = runner.invoke(cli, ["config", "init"])

        assert result.exit_code == 0
        assert (temp_config_dir / "config.yaml").exists()

    def test_config_show(self, runner, temp_config_dir, monkeypatch):
        """Test config show command."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "CONFIG_FILE", temp_config_dir / "config.yaml")

        # Create config first
        config = {"provider": "ollama", "model": "llama3.2"}
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "ollama" in result.output

    def test_config_set(self, runner, temp_config_dir, monkeypatch):
        """Test config set command."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "CONFIG_FILE", temp_config_dir / "config.yaml")

        result = runner.invoke(cli, ["config", "set", "provider", "openai"])

        assert result.exit_code == 0

        # Verify config was updated
        config_file = temp_config_dir / "config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)
            assert config["provider"] == "openai"

    def test_config_list_profiles(self, runner, temp_config_dir, monkeypatch):
        """Test config list - profiles command."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "PROFILES_FILE", temp_config_dir / "profiles.yaml")

        # Create profiles
        profiles = {
            "dev": {"provider": "ollama", "model": "llama3.2"},
            "prod": {"provider": "openai", "model": "gpt - 4"},
        }
        profiles_file = temp_config_dir / "profiles.yaml"
        with open(profiles_file, "w") as f:
            yaml.dump(profiles, f)

        result = runner.invoke(cli, ["config", "list - profiles"])

        assert result.exit_code == 0
        assert "dev" in result.output
        assert "prod" in result.output


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_cli_with_profile(self, runner, temp_config_dir, monkeypatch):
        """Test CLI with profile option."""
        import cli

        monkeypatch.setattr(cli, "CONFIG_DIR", temp_config_dir)
        monkeypatch.setattr(cli, "PROFILES_FILE", temp_config_dir / "profiles.yaml")

        # Create profile
        profiles = {"test": {"provider": "ollama", "model": "test - model"}}
        profiles_file = temp_config_dir / "profiles.yaml"
        with open(profiles_file, "w") as f:
            yaml.dump(profiles, f)

        result = runner.invoke(cli, ["--profile", "test", "--help"])

        assert result.exit_code == 0

    def test_cli_verbose_mode(self, runner):
        """Test CLI verbose mode."""
        result = runner.invoke(cli, ["--verbose", "--help"])

        assert result.exit_code == 0

    def test_cli_quiet_mode(self, runner):
        """Test CLI quiet mode."""
        result = runner.invoke(cli, ["--quiet", "--help"])

        assert result.exit_code == 0


class TestHelperFunctions:
    """Test helper functions for code generation."""

    def test_generate_main_file(self):
        """Test main file generation."""
        from cli import _generate_main_file

        content = _generate_main_file(
            name="TestProject",
            description="Test Description",
            provider="ollama",
            template="basic",
            num_agents=3,
            use_memory=True,
            use_tools=False,
        )

        assert "TestProject" in content
        assert "Test Description" in content
        assert "OllamaProvider" in content
        assert "range(3)" in content

    def test_generate_config(self):
        """Test config file generation."""
        from cli import _generate_config

        content = _generate_config(provider="openai", template="research")

        assert "openai" in content
        assert "research" in content

    def test_generate_requirements(self):
        """Test requirements file generation."""
        from cli import _generate_requirements

        content = _generate_requirements(
            provider="openai", use_memory=True, use_tools=True, use_plugins=True
        )

        assert "agentmind" in content
        assert "litellm" in content
        assert "chromadb" in content

    def test_generate_readme(self):
        """Test README generation."""
        from cli import _generate_readme

        content = _generate_readme(
            name="TestProject", description="Test Description", provider="ollama", template="basic"
        )

        assert "TestProject" in content
        assert "Test Description" in content
        assert "basic" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
