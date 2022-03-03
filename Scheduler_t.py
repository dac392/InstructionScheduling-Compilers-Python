from InstructionList_t import InstructionList_t
class Scheduler_t:
	def Scheduler_t(self, mode, instructions):
		self.mode = mode
		self.raw_instructions = []
		self.scheduled_instructions = []

	def schedule(self):
		execute = {"-a":self.longest_latency, "-b":self.highest_latency, "-c":self.my_own};
		statement = execute[self.mode]()
		return statement

	def longest_latency(self):
		IL = InstructionList()
		for line in self.instructions:
			IL.add_instruction(line)
		IL.print_instructions()