class BaseHttpException(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __len__(self):
        return 1
