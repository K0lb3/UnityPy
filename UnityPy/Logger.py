import logging
import sys

from termcolor import colored


if sys.platform == 'win32':
	from colorama import init
	init()


COLORS = {
	'DEBUG': 'green',
	'INFO': 'yellow',
	'WARNING': 'magenta',
	'ERROR': 'red',
}


class ListHandler(logging.Handler):
	def __init__(self):
		super().__init__()
		self.logs = []

	def emit(self, record):
		self.logs.append(record)


class ColoredFormatter(logging.Formatter):
	def format(self, record):
		msg = super().format(record)
		levelname = record.levelname
		if levelname in COLORS:
			msg = colored(msg, COLORS[levelname])
		return msg
