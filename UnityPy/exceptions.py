class TypeTreeError(Exception):
    def __init__(self, message, nodes):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.nodes = nodes