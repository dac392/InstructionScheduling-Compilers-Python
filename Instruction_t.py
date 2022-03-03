class Instruction_t:
	def __init__ (self, f_inst, inst_num, base_late, inst_type):
		self.instruction = f_inst
		self.instruction_number = inst_num
		self.base_latency = base_late
		self.fix_latency = 0
		self.individual_weight = 0
		self.type = inst_type
		self.next = None

	def get_keyword(self):
		return self.instruction.split(" ")[0]
	def get_instruction(self):
		return self.instruction.split(" ")
	def get_writable(self):
		return self.instruction.split(" ")[3]
	def get_readable(self):
		return self.instruction.split(" ")[1]
	def get_latency(self):
		if self.fix_latency > 0:
			return self.fix_latency
		return self.base_latency
	def is_leaf(self):
		ins = self.get_keyword()
		if ins == "loadI":
			return True
		return False
	def is_terminal(self):
		if self.next is None and self.type != "io" and self.instruction_number != 0:
			return True
		return False