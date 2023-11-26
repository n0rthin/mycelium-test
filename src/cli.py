import os
import typer
from src.scenario import get_scenarios
from src.test_runner import import_test_runner
from src.config import MycConfig
from rich import print

app = typer.Typer(invoke_without_command=True)

@app.callback()
def main():
    config = MycConfig()
    config.root_dir = os.getcwd()

    scenarios = get_scenarios(config)

    for scenario_path, scenario in scenarios:
        print(f"Running scenario ./{os.path.relpath(scenario_path, config.root_dir)}")
        test_runner_cls = import_test_runner(scenario.test_runner_path)
        test_runner = test_runner_cls(scenario)
        test_runner.run()


if __name__ == "__main__":
    app()