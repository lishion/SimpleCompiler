import logging
import sys
from runtime.interpreter import  INTERPRETER
from utils.logger import LOGGER

if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as f:
        code = f.read()
        LOGGER.setLevel(logging.WARNING)
        INTERPRETER.init()
        INTERPRETER.run(code)