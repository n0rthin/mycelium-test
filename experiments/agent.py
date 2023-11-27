import os
import time
import json
import threading
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Agent:
    def __init__(self, id, system_prompt, tools_service, allowed_tools):
        self.id = id
        self.tools_service = tools_service
        self.allowed_tools = allowed_tools
        self.system_prompt = system_prompt
        self.messages = []
        self.stopped = False
        self.is_running = False
        self.last_logger_message_index = None
        self.latest_processed_messages = None

    def init(self):
        self.log("Initializing agent")

        threading.Thread(target=self.run).start()

    def send_message(self, message):
        self.log("Adding message to thread")
        if len(self.messages) == 0:
            self.messages.append({
                "content": self.system_prompt,
                "role": "system"
            })

        self.messages.append({
            "content": message,
            "role": "user"
        })

    def run(self):
        while True:
            if self.stopped:
                break
            elif self.is_running:
                continue

            messages_to_process = len([message for message in self.messages if dict(message)["role"] != "assistant"])
            if messages_to_process > 0 and (self.latest_processed_messages is None or self.latest_processed_messages < messages_to_process):
                self.latest_processed_messages = messages_to_process
                self.process_message()

            time.sleep(1)

    def stop(self):
        self.log("Stopping agent")
        self.stopped = True

    def process_message(self):
        self.log_messages()

        self.is_running = True
        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=self.messages,
                tools=self.tools_service.get_tools_specs(self.allowed_tools)
            )
        except Exception as e:
            for message in self.messages:
                print(message)
            raise e

        new_message = completion.choices[0].message
        self.messages.append(new_message)
    
        if new_message.tool_calls:
            for tool_call in new_message.tool_calls:
                self.log("Tool call: {}".format(tool_call.function.name))
                if tool_call.function.name not in self.tools_service.tools:
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": "Unknown tool",
                    })

                try:
                    params = json.loads(tool_call.function.arguments)
                except:
                    self.log("invalid args: " + tool_call.function.arguments)
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": "Invalid params",
                    })

                if params:
                    self.log("Tool call params: {}".format(params))
                    result = self.tools_service.execute_tool(self.id, tool_call.function.name, params)
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": result or "",
                    })

        self.log_messages()
        self.is_running = False

    def log(self, message):
        print("[{}]: {}".format(self.id, message))

    def log_messages(self):
        for idx, message in enumerate(self.messages):
            message = dict(message)
            if self.last_logger_message_index is None or idx > self.last_logger_message_index:
                is_tool_call = ":tool_call" if "tool_calls" in message and message["tool_calls"] else ""
                self.log('=' * 20 + self.id + ":" + message["role"] + is_tool_call + '=' *  20)
                self.log(message["content"])
                self.last_logger_message_index = idx


class ToolsService:
    def __init__(self):
        self.tools = {}

    def register_tool(self, name, description, parameters, func):
        self.tools[name] = Tool(name, description, parameters, func)

    def get_tools_specs(self, tools = None):
        return [tool.get_spec() for tool in self.tools.values() if tools is None or tool.name in tools]

    def execute_tool(self, agent_id, name, params):
        return self.tools[name].run(agent_id, params)


class Tool:
    def __init__(self, name, description, parameters, func):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def run(self, agent_id, params):
        return self.func(_agent_id=agent_id, **params)
    
    def get_spec(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }