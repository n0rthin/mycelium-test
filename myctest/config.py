from typing import Optional

class MycConfig:
    iterraions: Optional[int] = 1
    timeout_sec: Optional[int] = 60
    wait_for_agents: Optional[bool] = False
    default_test_runner_path: Optional[str]
    root_dir: Optional[str]
    # scenarios_configs_patterns: Optional[list[str]] = ["!/**/venv/*.myc-scenario.yml"]
    scenarios_configs_patterns: Optional[list[str]] = [r'^(?!.*\/venv\/).*\.myc-scenario\.yml$']