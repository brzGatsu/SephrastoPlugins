from Core.Regel import Regel

def extend_regel():
    """
    Extends the Regel class with XML serialization support for Foundry VTT attributes.
    This is called when the plugin is initialized.
    """
    # Store the original serialize and deserialize methods
    original_serialize = Regel.serialize
    original_deserialize = Regel.deserialize

    def serialize_extended(self, ser):
        # First call the original serialize method
        original_serialize(self, ser)

        # Add Foundry VTT attributes if they exist
        if hasattr(self, 'foundry_modifications'):
            if self.foundry_modifications is not None:
                ser.set('foundry_modifications', self.foundry_modifications)
            ser.set('foundry_verteidigung', "1" if self.foundry_verteidigung else "0")
            ser.set('foundry_icon', self.foundry_icon or "")
            ser.set('foundry_input', self.foundry_input or "{}")

    def deserialize_extended(self, ser, referenceDB=None):
        # First call the original deserialize method
        original_deserialize(self, ser, referenceDB)

        # Initialize default values
        self.foundry_modifications = None
        self.foundry_verteidigung = False
        self.foundry_icon = "icons/svg/item-bag.svg"  # Default icon
        self.foundry_input = "CHECKBOX"  # Default input type

        # Load Foundry VTT attributes if they exist
        modifications = ser.get('foundry_modifications')
        if modifications:
            self.foundry_modifications = modifications

        self.foundry_verteidigung = ser.getBool('foundry_verteidigung', False)
        self.foundry_icon = ser.get('foundry_icon', 'icons/svg/item-bag.svg')
        self.foundry_input = ser.get('foundry_input', 'CHECKBOX')

    # Replace the original methods with our extended versions
    Regel.serialize = serialize_extended
    Regel.deserialize = deserialize_extended 