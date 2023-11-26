import os
import glob
import yaml
from typing import Optional, List, Dict
import schema
from src.config import MycConfig

class WithMetadata:
    metadata: Optional[Dict]

class AgentMessage(WithMetadata):
    content: str
    
class ScenarioAgentConfig(WithMetadata):
    system_prompt: str
    tools: Optional[List[str]] = None
    messages: Optional[List[AgentMessage]] = None

class EnvironmentConfig(WithMetadata):
    default_state: Optional[dict] = None
    desired_state_schema: Optional[dict] = None

class Scenario(WithMetadata):
    name: str
    description: Optional[str] = None
    timeout_sec: Optional[int] = 60
    iterations: Optional[int] = 1
    wait_for_agents: Optional[bool] = False
    test_runner_path: Optional[str] = None
    agents: List[ScenarioAgentConfig]
    environment: EnvironmentConfig

scenario_config_schema = schema.Schema(
    {
        "name": schema.And(str, len),
        schema.Optional("description"): str,
        schema.Optional("iterations"): schema.And(
            int,
            lambda iterations: iterations >= 1,
        ),
        schema.Optional("timeout_sec"): schema.And(
            int,
            lambda timeout_sec: timeout_sec >= 0,
        ),
        schema.Optional("wait_for_agents"): bool,
        schema.Optional("metadata"): schema.Or(dict, None),
        schema.Optional("test_runner_path"): str,
        "agents": [
            {
                "system_prompt": str,
                schema.Optional("tools"): [str],
                schema.Optional("messages"): [
                    {
                        "content": str,
                        schema.Optional("metadata"): schema.Or(dict, None),
                    }
                ],
                schema.Optional("metadata"): schema.Or(dict, None),
            }
        ],
        "environment": {
            schema.Optional("default_state"): dict,
            schema.Optional("desired_state_schema"): dict,
            schema.Optional("metadata"): schema.Or(dict, None),
        }
    }
)

def get_scenarios(myc_config: MycConfig) -> list[(str, Scenario)]:
    scenarios = []
    for file_path, scenario_config in load_scenarios(myc_config.root_dir, myc_config.scenarios_configs_pattern):
        fill_scenario_with_defaults(scenario_config, myc_config)
        validate_scenario(file_path, scenario_config)
        scenarios.append((file_path, create_scenario(scenario_config, file_path, myc_config)))

    return scenarios
       
def create_scenario(scenario_config: dict, scenario_file_path: str, myc_config: MycConfig) -> Scenario:
    scenario = Scenario()
    scenario.name = scenario_config.get("name")
    scenario.description = scenario_config.get("description")
    scenario.timeout_sec = scenario_config.get("timeout_sec")
    scenario.iterations = scenario_config.get("iterations")
    scenario.wait_for_agents = scenario_config.get("wait_for_agents")
    scenario.metadata = scenario_config.get("metadata")
    scenario.test_runner_path = os.path.normpath(os.path.join(os.path.dirname(scenario_file_path), scenario_config["test_runner_path"]))
    scenario.environment = EnvironmentConfig()
    scenario.environment.default_state = scenario_config.get("environment", {}).get("default_state")
    scenario.environment.desired_state_schema = scenario_config.get("environment", {}).get("desired_state_schema")
    scenario.environment.metadata = scenario_config.get("environment", {}).get("metadata")
    scenario.agents = []
    for agent_config in scenario_config["agents"]:
        agent = ScenarioAgentConfig()
        agent.system_prompt = agent_config.get("system_prompt")
        agent.tools = agent_config.get("tools")
        agent.messages = []
        for message_config in agent_config.get("messages", []):
            message = AgentMessage()
            message.content = message_config["content"]
            message.metadata = message_config.get("metadata")
            agent.messages.append(message)
        agent.metadata = agent_config.get("metadata")
        scenario.agents.append(agent)

    return scenario

def fill_scenario_with_defaults(scenario_config: dict, myc_config: MycConfig):
    if "iterations" not in scenario_config:
        scenario_config["iterations"] = myc_config.iterations

    if "timeout_sec" not in scenario_config:
        scenario_config["timeout_sec"] = myc_config.timeout_sec

    if "wait_for_agents" not in scenario_config:
        scenario_config["wait_for_agents"] = myc_config.wait_for_agents

    if "test_runner_path" not in scenario_config:
        scenario_config["test_runner_path"] = myc_config.default_test_runner_path

def load_scenarios(directory, pattern):
    scenarios = []

    for file_path in get_scenarios_paths(directory, pattern):
        with open(file_path, "r") as stream:
            parsed_scenario = yaml.safe_load(stream)
            scenarios.append((file_path, parsed_scenario))

    return scenarios

def validate_scenario(file_path, scenario_config: dict):
    try:
        scenario_config_schema.validate(scenario_config)
        if scenario_config["test_runner_path"]:
            if not scenario_config["test_runner_path"].endswith('.py'):
                raise Exception("Test runner file must be a python file: %s" % scenario_config["test_runner_path"])
            
            test_runner_path = os.path.join(os.path.dirname(file_path), scenario_config["test_runner_path"])
            if not os.path.isfile(test_runner_path):
                raise Exception("Test runner file not found: %s" % scenario_config["test_runner_path"])
    except Exception as e:
        print("Scenario config is invalid: %s" % file_path)
        raise e

def get_scenarios_paths(directory, pattern):
    for root, _, files in os.walk(directory):
        for file in glob.fnmatch.filter(files, pattern):
            yield os.path.join(root, file)

