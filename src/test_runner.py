import importlib
import sys
import os
from abc import ABC, abstractmethod
from src.scenario import Scenario
from src.environment import Environment
import time
import threading

class BaseTestRunner(ABC):
    def __init__(self, scenario: Scenario):
        self.wait_for_agents = scenario.wait_for_agents
        self.scenario = scenario
        self.environment = Environment(scenario.environment)
    
    def run(self, timeout_sec=20):
        self.before(self.scenario, self.environment)
        threading.Thread(target=self.run_agents).start()
        start = time.time()

        passed = False
        while True:
            elapsed = time.time() - start
            passed = self.run_tests()

            if passed and self.wait_for_agents is False:
                self.stop_agents()
                return {"passed": passed, "timeout": False, "time": elapsed}
            
            if self.agents_are_running() is False:
                return {"passed": passed, "timeout": False, "time": elapsed}
            
            if timeout_sec is not None and time.time() - start > timeout_sec:
                self.stop_agents()
                return {"passed": passed, "timeout": True, "time": elapsed}
            
            time.sleep(0.1)

    def run_tests(self):
        passed = self.environment.validate_state()
        for test in self.get_test_methods():
            passed = test(self)
        return passed
    
    def get_test_methods(cls):
        return [getattr(cls, func) for func in dir(cls) if callable(getattr(cls, func)) and func.startswith('test')]

    @abstractmethod
    def agents_are_running(self):
        pass
    
    @abstractmethod
    def before(self):
        pass

    @abstractmethod
    def after(self):
        pass
    
    @abstractmethod
    def run_agents(self):
        pass

    @abstractmethod
    def stop_agents(self):
        pass


def import_test_runner(module_path: str):
    spec = importlib.util.spec_from_file_location("test_runner", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    cls = module.TestRunner
    if not issubclass(cls, BaseTestRunner):
        raise Exception("TestRunner class must inherit from BaseTestRunner: %s" % module_path)
    
    return cls