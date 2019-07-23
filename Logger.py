from enum import Enum
from colorama import init
from termcolor import colored

init()


class LoggerEvent(Enum):
	Verbose = 0,
	Debug = 1,
	Info = 2,
	Warning = 3,
	Error = 4
	
	def print(self, string):
		COLOR = {
				'Verbose': 'white',
				'Debug'  : 'green',
				'Info'   : 'yellow',
				'Warning': 'magenta',
				'Error'  : 'red'
		}
		print(colored(f"{self.name}: {string}", COLOR[self.name]))


class Logger():
	log = []
	
	def Log(self, event: LoggerEvent, message: str):
		event.print(message)
		self.log.append((event, message))
	
	def Verbose(self, message: str):
		self.Log(LoggerEvent.Verbose, message)
	
	def Debug(self, message: str):
		self.Log(LoggerEvent.Debug, message)
	
	def Info(self, message: str):
		self.Log(LoggerEvent.Info, message)
	
	def Warning(self, message: str):
		self.Log(LoggerEvent.Warning, message)
	
	def Error(self, message: str):
		self.Log(LoggerEvent.Error, message)
