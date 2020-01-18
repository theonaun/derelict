import hashlib
import sys

from PyQt5.Qt import QObject

from .error import BricktonError


class Codec(QObject):

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.VERSION = parent.VERSION
        self._parent = parent
        self._km = parent.key_manager

    def encode(self, plaintext_message_bytes):
        '''This takes data and encodes it for transmission.'''
        # Create bytes and hash of bytes.
        length = len(plaintext_message_bytes)
        # Create hash
        plaintext_hash_bytes = hashlib.sha256(plaintext_message_bytes).digest()
        # Get keys.
        message_key, hash_key = self._km.compose_outbound_keys(length)
        # Create ciphertext
        ciphertext = bytes([data ^ mask
                            for data, mask
                            in zip(plaintext_message_bytes, message_key)])
        # Create cipherhash
        cipherhash = bytes([data ^ mask
                            for data, mask
                            in zip(plaintext_hash_bytes, hash_key)])
        # Return 
        return (ciphertext, cipherhash)

    def decode(self, ciphertext_message_bytes, ciphertext_hash_bytes):
        '''This takes ciphertext and decodes.'''
        length = len(ciphertext_message_bytes)
        # Get keys.
        message_key, hash_key = self._km.compose_inbound_keys(length)
        # Reconstitute text
        plaintext = bytes([data ^ mask
                           for data, mask
                           in zip(ciphertext_message_bytes, message_key)])
        # Recreate bytes.
        plainhash = bytes([data ^ mask
                           for data, mask
                           in zip(ciphertext_hash_bytes, hash_key)])
        # Check hash
        from_plaintext = hashlib.sha256(plaintext).digest()
        from_hash = plainhash
        if from_plaintext != from_hash:
            raise BricktonError('Defective hash accompanying message.')
        # Return
        return plaintext

    def static_encode(self):
        pass

    def static_decode(self):
        pass
