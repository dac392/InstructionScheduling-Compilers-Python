from Instruction_t import Instruction_t
from Parser_t import Parser_t
class InstructionList_t:
	def __init__ (self):
		# self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[3, "arithmatic"], "div":[3, "arithmatic"]}
		# self.memory_latencies = {"load":[5,"load1"], "loadI":[1,"load2"],"loadAI":[5,"load2"], "store":[5,"memory"], "storeAI":[5,"memory"]}
		# self.io_latencies = {"outputAI":[1,"io"]}

		self.parser = Parser_t()
		
		self.inst_counter = 0
		self.total_line_counter = 0
		self.instructions = {}
		self.instruction_lookup = {}
		self.anti_dependencies = {}
		self.path_weights = []
		self.scheduled = []

	def add_instruction(self, raw_instruction):
		# [inst_f, late, type]
		inst_info = self.parser.parse_instruction(raw_instruction, self.inst_counter)
		new_instruction = Instruction_t(inst_info[0], self.inst_counter, inst_info[1], inst_info[2])
		if new_instruction.is_leaf():
			self.instructions.update({self.total_line_counter : new_instruction})
			self.instruction_lookup.update({new_instruction.instruction_number : self.total_line_counter})
			self.path_weights.append(new_instruction.get_latency())
			self.parser.update_registers(new_instruction.get_writable(), [self.total_line_counter])
			self.total_line_counter+=1 # THIS MUST BE THE LAST LINE
		else:
			chain_keys = self.parser.find_branches(new_instruction.get_instruction())
			#print(chain_keys)
			for index,key in enumerate(chain_keys):
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
				if sep_instruction.type != "io" and index == 0:
					writable = sep_instruction.get_writable()
					self.parser.update_registers(writable, [key]) #change to chain_keys
					self.instruction_lookup.update({new_instruction.instruction_number : key})
				else:
					#print(chain_keys)
					for i in chain_keys:
						if i != key:
							self.path_weights[i] += sep_instruction.get_latency()
					break

		# exiting statements
		self.parser.find_potential_anti(new_instruction.instruction, new_instruction.instruction_number)
		self.inst_counter+=1

	def find_anti_dependence(self):
		# print(self.instruction_lookup)
		for key,chain in self.instructions.items():
			ptr = chain
			while(ptr is not None):
				if ptr.instruction in self.parser.potential_dependencies:
					dep_info = self.parser.potential_dependencies[ptr.instruction]
					if self.instruction_lookup[dep_info[2]] is not self.instruction_lookup[ptr.instruction_number]:
						self.anti_dependencies.update({ptr.instruction : dep_info[0]})
				ptr = ptr.next
		# print(self.anti_dependencies)

	
	def print_instructions(self):
		print("------------------start------------------")
		for key,chain in self.instructions.items():
			chain_string = []
			pointer = chain
			while pointer is not None:
					chain_string.append(pointer.instruction)
					pointer = pointer.next
			chain_string.append("Null")
			s = "---> ".join(chain_string)
			print(str(key)+": "+s)
		print(self.path_weights)
		print(self.anti_dependencies)
		print("------------------end------------------")




