from abc import ABC, abstractmethod


class ModelInterface(ABC):
    @abstractmethod
    def load_model(self, model_info):
        pass

    @abstractmethod
    def run_model(self, input_data):
        pass

    @abstractmethod
    def remove_model(self):
        pass

    @abstractmethod
    def display_interface(self, root):
        pass