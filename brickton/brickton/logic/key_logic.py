
from PyQt5.Qt import QObject
from PyQt5.Qt import QFileDialog
from PyQt5.Qt import QEvent


class KeyLogic(QObject):
    '''Handles key generation.'''

    # No signals. Key manager makes singals.

    def __init__(self, application):
        QObject.__init__(self, application)
        self._app = application
        self._ui = application.ui_main_window
        self._km = application.key_manager

    def setup(self):
        # Load initial keylist
        self._update_listkey([key.name
                              for key
                              in self._km.get_all_keys()])
        # Connect click to data update.
        self._ui.k_listkey_list.currentItemChanged.connect(self._select_key)
        # Select first row.
        self._ui.k_listkey_list.setCurrentRow(0)
        # Hide progress bar.
        self._ui.k_genprogress_bar.setHidden(True)
        # Load initial senders
        self._ui.k_sender_combo.addItems(self._km.get_senders())
        # Load initial receivers
        self._ui.k_receiver_combo.addItems(self._km.get_receivers())
        # Sort by sender connect
        self._ui.k_sender_combo.activated.connect(self._sort_sender)
        # Sort by receiever connect.
        self._ui.k_receiver_combo.activated.connect(self._sort_receiver)
        # Prime initial semder subset with values
        self._km.sort_by_sender(self._ui.k_sender_combo.currentText())
        # Prime initial semder subset with values
        self._km.sort_by_receiver(self._ui.k_receiver_combo.currentText())
        # Populate export combo boxes. Double call, but clearer this way.
        for combo_box in [self._ui.k_export1_combo,
                          self._ui.k_export2_combo]:
            senders = self._km.get_senders()
            receivers = self._km.get_receivers()
            # Add lists together
            senders.extend(receivers)
            all_parties = set(senders)
            combo_box.addItems(all_parties)
        # Populate random source
        random_sources = self._km.get_random_sources()
        self._ui.k_random_combo.addItems(random_sources)
        self._ui.k_random_combo.setCurrentIndex(0)
        # Connect export button with function.
        self._ui.k_export_button.clicked.connect(self._export_keys)
        # Connect import button with function.
        self._ui.k_import_button.clicked.connect(self._import_keys)
        # Connect key_manager.consolde_update to console.
        self._km.console_update.connect(self._update_console)
        # Connect update function with key manager update singal.
        self._km.keylist_update.connect(self._on_keymanager_update)
        # Connect key generation button with generate.
        self._ui.k_generate_button.clicked.connect(self._generate_keys)
        # Connect cancel button to cancel function.
        self._ui.k_cancel_button.clicked.connect(self._cancel_generation)

    def _update_console(self, update_text):
        self._ui.k_console_textedit.append(update_text)

    def _export_keys(self):
        party_1 = self._ui.k_export1_combo.currentText()
        party_2 = self._ui.k_export2_combo.currentText()
        self._km.export_keys(party_1, party_2)

    def _import_keys(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        folder = dialog.getExistingDirectory(caption="Select Directory")
        self._km.import_keys(folder)

    def _sort_sender(self, index):
        sender_name = self._ui.k_sender_combo.currentText()
        self._km.sort_by_sender(sender_name)
        names = self._km.get_subset_key_names()
        self._update_listkey(names)

    def _sort_receiver(self, index):
        receiver_name = self._ui.k_receiver_combo.currentText()
        self._km.sort_by_receiver(receiver_name)
        names = self._km.get_subset_key_names()
        self._update_listkey(names)

    def _update_listkey(self, name_list):
        self._ui.k_listkey_list.clear()
        self._ui.k_listkey_list.addItems(name_list)

    def _select_key(self, current_key, previous_key):
        # Get key data
        if current_key:
            key_dict = self._km.get_key_data(current_key.text())
        else:
            key_dict = {'sender'  : '',
                        'receiver': '',
                        'created' : '',
                        'length'  : '',
                        'position': '',
                        'name'    : ''}
        self._update_key_lines(**key_dict)

    def _update_key_lines(self, **kwargs):
        # Wipe lines nad insert text.
        for widget in [self._ui.k_listsender_line,
                       self._ui.k_listreceiver_line,
                       self._ui.k_listremaining_line,
                       self._ui.k_timestamp_line]:
            widget.clear()
        self._ui.k_listsender_line.insert(kwargs['sender'])
        self._ui.k_listreceiver_line.insert(kwargs['receiver'])
        try:
            remaining = kwargs['length'] - kwargs['position']
        except TypeError:
            remaining = ''
        self._ui.k_listremaining_line.insert(str(remaining))
        self._ui.k_timestamp_line.insert(str(kwargs['created']))

    def _on_keymanager_update(self):
        # Save current item for later.
        saved_current_item = self._ui.k_listkey_list.currentItem()
        # Sort by sender
        sender_name = self._ui.k_sender_combo.currentText()
        self._km.sort_by_sender(sender_name)
        # Sort by receiver
        receiver_name = self._ui.k_receiver_combo.currentText()
        self._km.sort_by_receiver(receiver_name)
        # Get names and update listkey.
        names = self._km.get_subset_key_names()
        self._update_listkey(names)
        # Update listkey.
        self._ui.k_listkey_list.clear()
        self._ui.k_listkey_list.addItems(names)
        # Update list
        self._ui.k_listkey_list.setCurrentItem(saved_current_item)

    def _generate_keys(self):
        party_1 = self._ui.k_genparty1_line.text()
        party_2 = self._ui.k_genparty2_line.text()
        pairs_to_generate = self._ui.k_gennum_spinbox.value()
        random_source = self._ui.k_random_combo.currentText()
        cancellation_event = QEvent(QEvent.User)
        cancellation_event.ignore()
        # Cancel button linked at thread start time.
        self._km.generate_keys(party_1,
                               party_2,
                               pairs_to_generate,
                               random_source,
                               cancellation_event)

    def _cancel_generation(self):
        self._km.trigger_cancellation()
