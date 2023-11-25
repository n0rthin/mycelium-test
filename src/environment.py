from src.observable import Observable    

class EnvironmentState:
    def __init__(self):
        self.state = {
            "fs": {},
        }

    def set(self, key, value):
        self.state[key] = value

    def get(self, key):
        return self.state[key]
  

class Environment(Observable):
    def __init__(self):
        super().__init__(["action.executed"])
        self.actions = {}
        self.state = EnvironmentState()

    def register_action(self, action, cb):
        self.actions[action] = cb

    def execute_action(self, action, *attrs):
        if action not in self.actions:
            raise Exception("Action %s not supported" % action)
        
        self.actions[action](self, *attrs)
        self.emit("action.executed", action, *attrs)