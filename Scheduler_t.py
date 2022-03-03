from InstructionList_t import InstructionList_t
class Scheduler_t:
	def __init__ (self, mode, instructions):
		self.mode = mode
		self.raw_instructions = instructions
		self.scheduled_instructions = []

	def schedule(self):
		execute = {"-a":self.longest_latency, "-b":self.highest_latency, "-c":self.my_own};
		statement = execute[self.mode]()
		return statement

	def longest_latency(self):
		IL = InstructionList_t()
		for line in self.raw_instructions:
			IL.add_instruction(line)
		IL.find_anti_dependence()

		IL.print_instructions()
	def highest_latency(self):
		print("B")
	def my_own(self):
		print("C")