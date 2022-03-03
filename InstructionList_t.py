from Instruction_t import Instruction_t
from Parser_t import Parser_t
class InstructionList_t:
	def Instruction_t(self):
		# self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[3, "arithmatic"], "div":[3, "arithmatic"]}
		# self.memory_latencies = {"load":[5,"load1"], "loadI":[1,"load2"],"loadAI":[5,"load2"], "store":[5,"memory"], "storeAI":[5,"memory"]}
		# self.io_latencies = {"outputAI":[1,"io"]}

		self.parser = Parser_t()
		
		self.inst_counter = 0
		self.total_line_counter = 0
		self.instructions = {}
		self.path_weights = []
		self.scheduled = []

	def add_instruction(self, raw_instruction):
		# [inst_f, late, type]
		inst_info = self.parser.parse_instruction(raw_instruction, self.instructions_counter)
		new_instruction = Instruction_t(inst_info[0], self.inst_counter, inst_info[1], inst_info[2])
		if new_instruction.is_leaf():
			self.instructions.update({self.total_line_counter : new_instruction})
			self.path_weights.append(new_instruction.get_latency())
			self.parser.update_registers(new_instruction.get_writable(), [self.total_line_counter])
			self.total_line_counter+=1 # THIS MUST BE THE LAST LINE
		else:
			chain_keys = self.parser.find_branches(new_instruction.get_instruction())
			for key in chain_keys:
				# makes it into separate nodes: if you want to find all matchesm you can add that here
				sep_instruction = Instruction_t(inst_info[0], self.inst_counter, inst_info[1], inst_info[2])
				pointer = self.instructions[key]
				prev = None
				while(pointer.next is not None):
					if(prev is not None and pointer.instruction == prev.instruction):
						break
					prev = pointer
					pointer = pointer.next
				self.path_weights[key] += sep_instruction.get_latency()
				pointer.next = sep_instruction
				pointer = pointer.next
				if sep_instruction.type != "io":
					writable = sep_instruction.get_writable()
					self.parser.update_registers(writable, chain_keys)
				else:
					for i in chain_keys:
						self.path_weights[i] += sep_instruction.get_latency()
					break

		# exiting statements
		self.inst_counter+=1
	
	def print_instructions(self):
		print("------------------start------------------")
		for key,chains in self.instructions.items():
			chain_string = []
			pointer = chain
			chain = ""
			while pointer is not None:
					chain_string.append(pointer.instruction)
					pointer = pointer.next
			chain_string.append("Null")
			chain_string.join("---> ")
			print(str(key)+": "+str(chain_string))
		print(self.path_weights)
		print("------------------end------------------")




