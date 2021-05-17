class LayerMemory():
    def __init__(self):
        pass

class Layer():
    def __init__(self, memory):
        self.memory = memory

    def process_flow(self, message):
        print("DO NOT USE THIS INTERFACE")
        return None