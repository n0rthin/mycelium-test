from abc import ABC, abstractmethod
import time
import threading

class BaseTestRunner(ABC):
    def __init__(self, wait_for_agents=False):
        self.wait_for_agents = wait_for_agents
        pass
    
    def init(self):
        self.init_agents()
        return self
  
    def run(self, timeout_sec=20):
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

    @abstractmethod
    def run_tests(self):
        pass

    @abstractmethod
    def agents_are_running(self):
        pass
    
    @abstractmethod
    def init_agents(self):
        pass
    
    @abstractmethod
    def run_agents(self):
        pass

    @abstractmethod
    def stop_agents(self):
        pass
