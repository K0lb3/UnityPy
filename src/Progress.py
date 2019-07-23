class Progress():
	preValue: int
	
	def Reset(self):
		self.preValue = 0
		self.Report(0)
	
	def Report(self, current: int, total: int = None):
		if total:
			value = current * 100 // total
		else:
			value = current
		
		if value > self.preValue:
			self.preValue = value
			print(f'{value}%')
