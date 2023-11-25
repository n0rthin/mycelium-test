import uuid
from dotenv import load_dotenv
load_dotenv()

from src.test_runner import BaseTestRunner
from src.environment import Environment
from src.agent import Agent, ToolsService

agents = {}

agent_to_agent_message_template = '''===Incoming message===
agent_id: {sender_id}
message_content: 
{message}
===End of Incoming message from==='''

def send_message(_agent_id, agent_id, message):
    agents[agent_id].send_message(agent_to_agent_message_template.format(sender_id=_agent_id,message=message))
    return "Message sent. You will be notifed when reciever will respond."

def write_to_file(environment: Environment, filepath: str, content: str):
    print("Writing to file", filepath, content)
    environment.state.set("fs", { filepath: content})
    return "File written"

tools_service = ToolsService()
tools_service.register_tool(
    "send_message",
    "Sends message to another agent",
    {
        "type": "object",
        "properties": {
          "agent_id": {
            "type": "string",
            "description": "Id of the agent"
          },
          "message": {
            "type": "string",
            "description": "Your message"
          }
        }
    },
    send_message
)



class TestRunner(BaseTestRunner):
    def run_tests(self):
        return "filepath" in self.environment.state.get("fs") and self.environment.state.get("fs")["filepath"] == "Hello world"

    def init_agents(self):
        self.init_environment()
        # agent_a_id = str(uuid.uuid4())
        agent_a_id = "boss"
        # agent_b_id = str(uuid.uuid4())
        agent_b_id = "employee"
        self.agent_a = Agent(
            agent_a_id,
            '''You are a boss.
            Your goal is to change file content to 'Hello world'.
            File path is 'filepath'. You have an agent employee (id={agent_b_id}). You can delegate tasks to him by sending messsages.
            You can send message with send_message tool.'''.format(agent_b_id=agent_b_id),
            tools_service,
            ["send_message"]
        )
        self.agent_b =  Agent(
            agent_b_id,
            '''You are an employee.
            Your goal is execute any tasks given by Boss. Wait for messages from him.
            If you need report something to Boss, you can use send_message tool.
            If you want to change file content, you can use write_to_file tool.
            ''',
            tools_service,
            ["send_message", "write_to_file"]
            )
        agents[agent_a_id] = self.agent_a
        agents[agent_b_id] = self.agent_b

    def init_environment(self):
        self.environment = Environment()
        self.environment.register_action("write_to_file", write_to_file)
        def write_to_file_tool(_agent_id, filepath: str, content: str):
            self.environment.execute_action("write_to_file", filepath, content)
        tools_service.register_tool(
            "write_to_file",
            "Writes content to file",
            {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file"
                    },
                    "content": {
                        "type": "string",
                        "description": "File content"
                    }
                }
            },
            write_to_file_tool
        )
    
    def run_agents(self):
        self.agent_a.init()
        self.agent_b.init()
        self.agent_a.send_message("Begin")

    def stop_agents(self):
        self.agent_a.stop()
        self.agent_b.stop()

    def agents_are_running(self):
        return not (self.agent_a.stopped and self.agent_b.stopped)

    def init_agent(system):
        return Agent(str(uuid.uuid4()), system, tools_service)




result = TestRunner(wait_for_agents=False).init().run(timeout_sec=1000)
print(result)