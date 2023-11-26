import importlib.util as importutil
from src.scenario import Scenario
from src.environment import Environment
import time
from rich import print

class Iteration:
    def __init__(self, index: int):
        self.index = index

    passed: bool = False
    timeout: bool = False
    time: float = 0.0
    done: bool = False

    def __str__(self):
        return "passed=%s, timeout=%s, time=%f, done=%s" % (self.passed, self.timeout, self.time, self.done)

class BaseTestRunner():
    def __init__(self, scenario: Scenario):
        self.wait_for_agents = scenario.wait_for_agents
        self.scenario = scenario
        self.environment = Environment(scenario.environment)
    
    def run(self) -> list[Iteration]:
        self.before(self.scenario, self.environment)

        iterations = []
        for i in range(self.scenario.iterations):
            iteration = self.iteration(i)
            iterations.append(iteration)
            print("Iteration %d: %s" % (i, iteration))

        self.after(self.scenario, self.environment, iterations)

        return iterations

    def iteration(self, index):
        timeout_sec = self.scenario.timeout_sec
        iteration = Iteration(index)

        self.before_iteration(self.scenario, self.environment, iteration)
        
        start = time.time()
        passed = False
        while True:
            elapsed = time.time() - start
            timed_out = timeout_sec is not None and elapsed > timeout_sec
            passed = self.run_tests()

            if passed or timed_out:
                iteration.done = True
                iteration.passed = passed
                iteration.timeout = timed_out
                iteration.time = elapsed
                break
            
            time.sleep(0.1)

        self.after_iteration(self.scenario, self.environment, iteration)

        return iteration

    def run_tests(self):
        passed = self.environment.validate_state()
        for test in self.get_test_methods():
            passed = test(self)
        return passed
    
    def get_test_methods(cls):
        return [getattr(cls, func) for func in dir(cls) if callable(getattr(cls, func)) and func.startswith('test')]

    def before(self, _, __):
        pass

    def after(self, _, __, ___):
        pass

    def before_iteration(self, _, __, ___):
        pass

    def after_iteration(self, _, __, ___):
        pass


def import_test_runner(module_path: str):
    spec = importutil.spec_from_file_location("test_runner", module_path)
    module = importutil.module_from_spec(spec)
    spec.loader.exec_module(module)

    cls = module.TestRunner
    if not issubclass(cls, BaseTestRunner):
        raise Exception("TestRunner class must inherit from BaseTestRunner: %s" % module_path)
    
    return cls