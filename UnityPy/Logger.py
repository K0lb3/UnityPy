import time
from enum import Enum

from colorama import init
from termcolor import colored

init()

COLOR = {
	'Verbose': 'white',
	'Debug': 'green',
	'Info': 'yellow',
	'Warning': 'magenta',
	'Error': 'red'
}


class LoggerEvent(Enum):
	Verbose = 0,
	Debug = 1,
	Info = 2,
	Warning = 3,
	Error = 4

	def print(self, string):
		print(colored(f"{self.name}: {string}", COLOR[self.name]))


class Logger:
	log: list
	print: bool

	def __init__(self, print: bool = False):
		self.print = print
		self.log = []

	def _log(self, event: LoggerEvent, message: str):
		if self.print:
			event.print(message)
		self.log.append((event, message))

	def verbose(self, message: str):
		self._log(LoggerEvent.Verbose, message)

	def debug(self, message: str):
		self._log(LoggerEvent.Debug, f"{time.thread_time_ns()} - {message}")

	def info(self, message: str):
		self._log(LoggerEvent.Info, message)

	def warning(self, message: str):
		self._log(LoggerEvent.Warning, message)

	def error(self, message: str, error: Exception):
		self._log(LoggerEvent.Error, '\n'.join([message, str(error)]))
