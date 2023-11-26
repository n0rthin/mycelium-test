from src.observable import Observable    
from src.scenario import EnvironmentConfig

class EnvironmentState:
    def __init__(self, default_state = {}):
        self.state = default_state

    def set(self, key, value):
        self.state[key] = value

    def get(self, key):
        return self.state[key]
  

class Environment(Observable):
    def __init__(self, environment_config: EnvironmentConfig):
        super().__init__(["action.executed"])
        self.actions = {}
        self.state = EnvironmentState(environment_config.default_state)
        self.desired_state_schema = environment_config.desired_state_schema

    def register_action(self, action, cb):
        self.actions[action] = cb

    def execute_action(self, action, *attrs):
        if action not in self.actions:
            raise Exception("Action %s not supported" % action)
        
        self.actions[action](self, *attrs)
        self.emit("action.executed", action, *attrs)

    def validate_state(self):
        # TODO: validate state
        return True