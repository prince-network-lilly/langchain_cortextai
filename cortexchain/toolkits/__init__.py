"""Pre-built toolkits — curated tool collections for common workflows."""

from typing import List
from cortexchain.tools.base import BaseTool
from cortexchain.tools.python_repl import PythonREPLTool
from cortexchain.tools.http_request import HTTPRequestTool
from cortexchain.tools.file_system import ReadFileTool, WriteFileTool, ListDirectoryTool
from cortexchain.tools.sql_database import SQLDatabaseTool
from cortexchain.tools.data_validation import DataValidationTool
from cortexchain.tools.experiment_tracker import ExperimentTrackerTool
from cortexchain.tools.pipeline_monitor import PipelineMonitorTool
from cortexchain.tools.api_health import APIHealthCheckTool
from cortexchain.tools.shell import ShellTool


class BaseToolkit:
    """Base class for toolkits — a curated collection of tools for a specific domain."""

    name: str = ""
    description: str = ""

    def get_tools(self) -> List[BaseTool]:
        raise NotImplementedError


class MLOpsToolkit(BaseToolkit):
    """Tools for the ML operations lifecycle: experiments, validation, monitoring, deployment."""

    name = "mlops"
    description = "ML operations: experiment tracking, data validation, pipeline monitoring, health checks"

    def __init__(self, storage_dir: str = ".mlops"):
        self.storage_dir = storage_dir

    def get_tools(self) -> List[BaseTool]:
        return [
            DataValidationTool(),
            ExperimentTrackerTool(storage_dir=f"{self.storage_dir}/experiments"),
            PipelineMonitorTool(),
            APIHealthCheckTool(),
            PythonREPLTool(),
        ]


class DataToolkit(BaseToolkit):
    """Tools for data engineering: file I/O, SQL queries, validation, Python processing."""

    name = "data"
    description = "Data engineering: read/write files, query databases, validate data, run Python"

    def __init__(self, db_connection_string: str = None, base_dir: str = None):
        self.db_connection_string = db_connection_string
        self.base_dir = base_dir

    def get_tools(self) -> List[BaseTool]:
        tools = [
            ReadFileTool(base_dir=self.base_dir),
            WriteFileTool(base_dir=self.base_dir),
            ListDirectoryTool(base_dir=self.base_dir),
            PythonREPLTool(),
            DataValidationTool(),
        ]
        if self.db_connection_string:
            tools.append(SQLDatabaseTool(connection_string=self.db_connection_string))
        return tools


class DevToolkit(BaseToolkit):
    """Tools for software development: shell, file system, HTTP, Python REPL."""

    name = "dev"
    description = "Software development: shell commands, file operations, HTTP requests, Python execution"

    def __init__(self, allowed_commands: list = None, base_dir: str = None):
        self.allowed_commands = allowed_commands
        self.base_dir = base_dir

    def get_tools(self) -> List[BaseTool]:
        return [
            ShellTool(allowed_commands=self.allowed_commands),
            ReadFileTool(base_dir=self.base_dir),
            WriteFileTool(base_dir=self.base_dir),
            ListDirectoryTool(base_dir=self.base_dir),
            HTTPRequestTool(),
            PythonREPLTool(),
        ]


class APIToolkit(BaseToolkit):
    """Tools for API interaction: HTTP requests, health checks, monitoring."""

    name = "api"
    description = "API interaction: make HTTP requests, check endpoint health, monitor services"

    def __init__(self, allowed_domains: list = None):
        self.allowed_domains = allowed_domains

    def get_tools(self) -> List[BaseTool]:
        return [
            HTTPRequestTool(allowed_domains=self.allowed_domains),
            APIHealthCheckTool(),
            PipelineMonitorTool(),
        ]
