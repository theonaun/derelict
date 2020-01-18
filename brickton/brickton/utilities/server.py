import base64
import hashlib
import io
import json
import time

from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QObject
from PyQt5.Qt import QHostAddress
from PyQt5.Qt import QTcpServer

from .error import BricktonError


class Server(QObject):
    '''Handles sockets. Should make client and server inherit from common base.'''

    # Emitted signals
    comm_update = pyqtSignal([str], name='communication_update')
    chat_update = pyqtSignal([dict], name='chat_update')
    client_connected = pyqtSignal(name='client_connected')
    handshake_succeded = pyqtSignal(name='handshake_succeeded')
    handshake_failed = pyqtSignal(name='handshake_failed')
    msg_ready = pyqtSignal([dict], name='msg_ready')
    comm_error = pyqtSignal(name='comm_error')

    # Signals listened to
    # data_ready = pyqtSignal([str, dict], name='data_ready')

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self._parent = parent
        self._km = parent.key_manager
        self._codec = parent.codec
        self._VERSION = parent.VERSION
        self._qsocket = None
        self._qserver = QTcpServer(self)
        self._bytestream = None
        self._other_party = None
        self._this_party = None
        self._ip_address = None
        self._port = None
        self._setup()
    
    def _setup(self):
        # Note socket connections cannot be done until a socket exists.
        # Connect qserver to connection callback.
        self._qserver.newConnection.connect(self._on_connection)
        # Prime the json generator
        self._msg_buffer = self._add_to_buffer()
        self._msg_buffer.send(None)
        # Connect self.msg_ready
        self.msg_ready.connect(self._dispatch_msg)
    
    def _server_handshake_1(self, msg_dict):
        # Server sends back list of shared keys as server handshake 1.
        foreign_key_set = set(msg_dict['data']['key_list'])
        local_key_set = set([key.name for key in self._km.get_all_keys()])
        shared_keys = list(local_key_set.intersection((foreign_key_set)))
        data_dict = {'shared_keys': shared_keys}
        server_msg_1 = self._create_json_msg('server_handshake_1',
                                             data_dict)
        self._qsocket.write(server_msg_1.encode())

    def _server_handshake_2(self, msg_dict):
        # Server send server handshake 2 after harmonizing.
        client_shared_key_data = msg_dict['data']['client_shared_key_data']
        # Set other party.
        self._other_party = msg_dict['metadata']['sender']
        client_key_names = [key_dict['name']
                            for key_dict
                            in client_shared_key_data]
        server_shared_key_data = [self._km.get_key_data(key)
                                  for key
                                  in client_key_names]
        harmonized_data = self._km.harmonize_keys(server_shared_key_data,
                                                  client_shared_key_data)
        for item in harmonized_data:
            if item['sender'] == self._this_party:
                self._km.add_to_outbound(item['name'])
            if item['sender'] == self._other_party:
                self._km.add_to_inbound(item['name'])
        server_msg_2 = self._create_json_msg('server_handshake_2',
                                             {'harmonized_data': harmonized_data})
        self._qsocket.write(server_msg_2.encode())
        # Wait for client to close connection.
        if not harmonized_data:
            self.comm_update.emit('No shared keys.')
            return False
        self.comm_update.emit('Server-side handshake complete.')
    
    def _on_connection(self):
        # QServer returns QSocket.
        self._qsocket = self._qserver.nextPendingConnection()
        # Ready read
        self._qsocket.readyRead.connect(self._on_ready_read)
        # On disconnection
        self._qsocket.disconnected.connect(self._on_disconnection)
        # Connect error to emit socket update.
        self._qsocket.error.connect(self._on_error)
        address = self._qsocket.peerAddress().toString()
        self.comm_update.emit('Connected to ' + address + '.')
        
    def _on_disconnection(self):
        self.comm_update.emit('Connection terminated.')
        self.comm_error.emit()

    def _on_error(self):
        self.comm_update.emit(self._qsocket.errorString() + '.')
        self.comm_error.emit()
        
    def _on_ready_read(self):
        data = self._qsocket.read(4096)
        self._msg_buffer.send(data)
        # Re-emit readyRead, quasi-recursive.
        if self._qsocket.bytesAvailable():
            self._qsocket.readyRead.emit()

    def _add_to_buffer(self):
        '''Generator created in _setup. Issues data via signal.'''
        # Set up constants.
        opener = '{' #123
        closer = '}' #125
        single_quote = '\'' # 39
        double_quote = '\"' # 34
        self._bytestream = io.BytesIO()
        inside_double_quote = False
        inside_single_quote = False
        opener_count = 0
        closer_count = 0
        # Repeat this loop until end of time.
        while True:
            # Given via generator.send method.
            raw_data = yield
            data = raw_data.decode('utf-8')
            for character in data:
                if character == single_quote:
                    # If True, False. If False, True.
                    inside_single_quote = not inside_single_quote
                if character == double_quote:
                    inside_double_quote = not inside_double_quote
                if inside_single_quote or inside_double_quote:
                    pass
                else:
                    if character == opener:
                        opener_count += 1
                    if character == closer:
                        closer_count += 1
                    if opener_count == closer_count:
                        # Write final character to bytestream
                        self._bytestream.write(character.encode())
                        # Complete JSON message.
                        json_msg = self._bytestream.getvalue().decode('utf-8')
                        msg = json.loads(json_msg)
                        self.msg_ready.emit(msg)
                        # Reset because it's a new message now.
                        self._bytestream = io.BytesIO()
                        inside_double_quote = False
                        inside_single_quote = False
                        opener_count = 0
                        closer_count = 0
                        # Back to "while True" loop
                        continue
                # Write to bytestream
                self._bytestream.write(character.encode())

    def listen_(self, identity, port):
        # If connected, disconnect.
        try:
            if self._qsocket.state == 3:
                self._qsocket.disconnectFromHost()
        except AttributeError:
            pass
        # Close qserver in case of repressing button
        self._qserver.close()
        self.comm_update.emit('Listening on port {}.'.format(port))
        self._this_party = identity
        self._qsocket = self._qserver.listen(QHostAddress.Any, int(port))

    def _dispatch_msg(self, msg_dict):
        '''Route message to correct function.'''
        msg_type = msg_dict['metadata']['type']
        routing_dict = {'text': self._recv_text,
                        'file': None,
                        'client_handshake_1': self._server_handshake_1,
                        'client_handshake_2': self._server_handshake_2}
        function_to_use = routing_dict[msg_type]
        function_to_use(msg_dict)

    def _recv_text(self, msg):
        ciphertext = msg['data']['ciphertext']
        cipherhash = msg['data']['cipherhash']
        ciphertext_bytes = base64.b64decode(ciphertext)
        cipherhash_bytes = base64.b64decode(cipherhash)
        try:
            plaintext = self._codec.decode(ciphertext_bytes, cipherhash_bytes)
        except BricktonError:
            self.comm_update.emit('Codec error. Likely insufficient keys.')
        chat_msg = {}
        chat_msg['content'] = plaintext.decode()
        chat_msg['source'] = self._other_party.decode()
        self.chat_update.emit(chat_msg)
                 
    def send_text(self, text_data):
        data_bytes = text_data.encode('utf-8')
        try:
            ciphertext, cipherhash = self._codec.encode(data_bytes)
        except BricktonError:
            self.comm_update.emit('Codec error. Likely insufficient keys.')
        data_dict = {'ciphertext': base64.b64encode(ciphertext),
                     'cipherhash': base64.b64encode(cipherhash)}
        msg = self._create_json_msg('text', data_dict)
        self._qsocket.write(msg.encode())
        self.chat_update.emit({'source': self._this_party,
                               'text': text_data})
    
    def _send_file(self, file_object):
        pass

    def _recv_file(self, output_path):
        pass

    def _create_json_msg(self, msg_type, data_dict):
        '''Create msg based on template (must be json serialize-able).'''
        base = {'metadata': {'brickton_version': self._VERSION,
                             'sender': self._this_party,
                             'receiver': self._other_party,
                             'timestamp': '{0:.7f}'.format(time.time()),
                             'encoding': 'base64',
                             'type': msg_type},
                'data':{}}
        # Types to check against.
        types = ['text',
                 'file',
                 'server_handshake_1',
                 'server_handshake_2', 
                 'client_handshake_1',
                 'client_handshake_2']
        # Type error checking.
        if not msg_type in types:
            raise BricktonError('Message type not valid.')
        # Keys by type.
        keys_by_type = {'text': ['ciphertext', 'cipherhash'],
                        'file': ['ciphertext', 'cipherhash', 'ciphername'],
                        'server_handshake_1': ['shared_keys'],
                        'server_handshake_2': ['harmonized_data'], 
                        'client_handshake_1': ['key_list'],
                        'client_handshake_2': ['client_shared_key_data']}
        # Keys by type error checking.
        for key in data_dict.keys():
            if not key in keys_by_type[msg_type]:
                raise BricktonError('Improper key supplied.')
        # Populate data dict.
        for key, value in data_dict.items():
            base['data'][key] = value
        # Create and return msg as json.
        msg_string = json.dumps(base)
        return msg_string

    def stop(self):
        self._qsocket.close()
        self.terminate()

