import sys
import traceback

class CustomException(Exception):
    def __init__(self, error_message: str, error_detail:sys):
        _, _, exc_tb = error_detail.exc_info()
        if exc_tb is not None:
            self.filename = exc_tb.tb_frame.f_code.co_filename
            self.lineno = exc_tb.tb_lineno
        else:
            self.filename = "<unknown>"
            self.lineno = 0
        self.error_message = str(error_message)
        self.traceback = ''.join(traceback.format_exception(*error_detail.exc_info()))

    def __str__(self):
        return f"Error occurred in file: {self.filename} at line: {self.lineno} with message: {self.error_message}\nTraceback: {self.traceback}"

# if __name__ == "__main__":
#     try:
#         a = 1 / 0
#     except Exception as e:
#         raise CustomException(e, sys)
