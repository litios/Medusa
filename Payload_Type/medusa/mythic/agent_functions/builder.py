from mythic_payloadtype_container.PayloadBuilder import *
from mythic_payloadtype_container.MythicCommandBase import *
import asyncio
import os
from distutils.dir_util import copy_tree
import tempfile
import base64

class Medusa(PayloadType):

    name = "medusa" 
    file_extension = "py"
    author = "@ajpc500"
    supported_os = [  
        SupportedOS.Windows, SupportedOS.Linux, SupportedOS.MacOS
    ]
    wrapper = False  
    wrapped_payloads = []  
    mythic_encrypts = True
    note = "This payload uses Python to create a simple agent"
    supports_dynamic_loading = True
    build_parameters = {
        "output": BuildParameter(
            name="output",
            parameter_type=BuildParameterType.ChooseOne,
            description="Choose output format",
            choices=["py", "base64"],
        ),
        "python_version": BuildParameter(
            name="python_version",
            parameter_type=BuildParameterType.ChooseOne,
            description="Choose Python version",
            choices=["Python 3.8", "Python 2.7"],
        )
    }
    c2_profiles = ["http"]
    translation_container = None
    support_browser_scripts = [
        BrowserScript(script_name="create_table", author="@its_a_feature_"),
        BrowserScript(script_name="copy_additional_info_to_clipboard", author="@djhohnstein"),
        BrowserScript(script_name="file_size_to_human_readable_string", author="@djhohnstein")
    ]

    def getPythonVersionFile(self, file):
        pyv = self.get_parameter("python_version")
        if os.path.exists(os.path.join(self.agent_code_path, "{}.py".format(file))):
            #while we've specified a python version, this function is agnostic so just return the .py
            return "{}.py".format(file)
        elif pyv == "Python 2.7":
            return "{}.py2".format(file)
        else:
            return "{}.py3".format(file)

    async def build(self) -> BuildResponse:
        # this function gets called to create an instance of your payload
        resp = BuildResponse(status=BuildStatus.Success)
        # create the payload
        try:
            command_code = ""
            for cmd in self.commands.get_commands():
                command_code += (
                    open(os.path.join(self.agent_code_path, "{}".format(self.getPythonVersionFile(cmd))), "r").read() + "\n"
                )
            base_code = open(
                os.path.join(self.agent_code_path, self.getPythonVersionFile("base_agent")), "r"
            ).read()
            base_code = base_code.replace("UUID_HERE", self.uuid)
            base_code = base_code.replace("#COMMANDS_HERE", command_code)
            for c2 in self.c2info:
                profile = c2.get_c2profile()["name"]
                for key, val in c2.get_parameters_dict().items():
                    if not isinstance(val, str):
                        base_code = base_code.replace(key, \
                            json.dumps(val).replace("false", "False").replace("true","True").replace("null","None"))
                    else:
                        base_code = base_code.replace(key, val)
            if self.get_parameter("output") == "base64":
                    resp.payload = base64.b64encode(base_code.encode())
                    resp.set_message("Successfully Built")
                    resp.status = BuildStatus.Success
            else:
                resp.payload = base_code.encode()
                resp.message = "Successfully built!"
        except Exception as e:
            resp.set_status(BuildStatus.Error)
            resp.set_message("Error building payload: " + str(e))
        return resp
