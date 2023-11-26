from typing import Optional

class MycConfig:
    iterraions: Optional[int] = 1
    timeout_sec: Optional[int] = 60
    wait_for_agents: Optional[bool] = False
    default_test_runner_path: Optional[str]
    root_dir: Optional[str]
    scenarios_configs_pattern: Optional[str] = "*.myc-scenario.yml"