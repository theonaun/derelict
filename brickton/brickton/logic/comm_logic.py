import datetime

from PyQt5.Qt import QObject
from PyQt5.Qt import QFileDialog
from PyQt5.Qt import QEvent


class CommunicationLogic(QObject):
    '''Handles communication generation.'''

    # No signals. Socket makes signals.

    def __init__(self, app):
        QObject.__init__(self, app)
        self._app = app
        self._ui = app.ui_main_window
        self._km = app.key_manager
        self._client = app.client
        self._server = app.server
        self._codec = app.codec
        self._role = None

    def setup(self):
        # Initial UI items.
        self._update_console('Setting up application.')
        self._ui.c_port_line.insert('8888')
        self._ui.c_ip_line.insert('0.0.0.0')
        # KM Populate identity comboboxes.
        self._update_identities()
        # KM Connect identities to update signal.
        self._km.keylist_update.connect(self._update_identities)
        # Connect connect button to connect
        self._ui.c_connect_button.clicked.connect(self._connect)
        # Connect listen button to _listen
        self._ui.c_listen_button.clicked.connect(self._listen)
        # Connect general client update to console.
        self._client.comm_update.connect(self._update_console)
        # Connect general server update to console.
        self._server.comm_update.connect(self._update_console)
        # Connect send button to _send_text
        self._ui.c_send_button.clicked.connect(self._send_text)
        # Setup
        self._update_console('Application ready.')
        # Error should refresh
        self._client.comm_error.connect(self._clear_all)
        # Connect general server update to console.
        self._server.comm_error.connect(self._clear_all)

    def _update_identities(self):
        # Update IDs in combo boxes.
        sender_identities = list(self._km.sender_identities)
        self._ui.c_local_combo.addItems(sender_identities)
        receiver_identities = list(self._km.receiver_identities)
        self._ui.c_foreign_combo.addItems(receiver_identities)

    def _update_console(self, update_text):
        self._ui.c_console.append(update_text)

    def _listen(self):
        '''Gives calling computer server role and listens for connection.'''
        # Get and validate port
        port = self._ui.c_port_line.text()
        valid_port = self._validate_port(port)
        # Get and validate IP.
        server_identity = self._ui.c_local_combo.currentText()
        if valid_port:
            self._clear_all()
            self._ui.c_role_line.setText('Server')
            self._role = 'server'
            self._ui.c_port_line.setText(str(port))
            self._server.listen_(server_identity, port)
            self._server.chat_update.connect(self._display_text)
        else:
            self._update_console('Invalid port.')

    def _connect(self):
        # Get and validate port
        port = self._ui.c_port_line.text()
        valid_port = self._validate_port(port)
        # Get and validate IP.
        ip = self._ui.c_ip_line.text()
        # Numeric IP is a bool that is passed to client.connect_
        numeric_ip = self._validate_ip(ip)
        client_identity = self._ui.c_local_combo.currentText()
        # Attach client
        self._ui.c_role_line.setText('Client')
        self._role = 'client'
        self._client.connect_(client_identity, ip, port, numeric=numeric_ip)
        self._client.chat_update.connect(self._display_text)

    def _clear_all(self):
        for widget in [self._ui.c_role_line,
                       self._ui.c_current_line,
                       self._ui.c_remaining_line,
                       self._ui.c_ip_line,
                       self._ui.c_port_line]:
            widget.clear()
    
    def _validate_ip(self, ip):
        # Turn off IP verification.
        for character in ip:
            is_digit = character.isdigit()
            is_dot = character == '.'
            if (is_digit or is_dot):
                pass
            else:
                self._ui.c_port_line.clear()
                self._ui.c_ip_line.clear()
                return False
        return True
    
    def _validate_port(self, port):
        try:
            port = int(port)
            if port < 1024:
                self._update_console('Invalid port (system port).')
                return False
            else:
                return True
        except ValueError:
            self._ui.c_port_line.clear()
            self._ui.c_ip_line.clear()
            self._update_console('Invalid port.')
            return False

    def _send_text(self):
        entered_text = self._ui.c_chat_input.toPlainText()
        self._ui.c_chat_input.clear()
        if self._role == 'server':
            # If connected
            if self._server._qsocket.state() == 3:
                self._server.send_text(entered_text)
            else:
                self._update_console('Not connected.')
        if self._role == 'client':
            # If connected
            if self._client._qsocket.state() == 3:
                self._client.send_text(entered_text)
            else:
                self._update_console('Not connected.')
    
    def _display_text(self, chat_data):
        update_string = '{source}@{time}\n{content}'.format(source=chat_data['source'],
                                                            time=datetime.datetime.now(),
                                                            content=chat_data['content'])
        self._ui.c_chat_output.append(update_string)

    # On client connect ... link display text with client.msg_ready
    # On server connect ... link display text with server.msg_ready

'''
# setText
# append
# text
c_chat_output
c_role_line
c_local_combo
c_foreign_comboe
c_current_line
c_remaining_line
c_ip_line
c_port_line
c_connect_button
c_listen_button
c_console
c_chat_input
c_send_button
c_upload_button
'''