from Instruction_t import Instruction_t
from Parser_t import Parser_t
class InstructionList_t:
	def __init__ (self):
		# self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[3, "arithmatic"], "div":[3, "arithmatic"]}
		# self.memory_latencies = {"load":[5,"load1"], "loadI":[1,"load2"],"loadAI":[5,"load2"], "store":[5,"memory"], "storeAI":[5,"memory"]}
		# self.io_latencies = {"outputAI":[1,"io"]}

		self.parser = Parser_t()
		
		self.inst_counter = 1
		self.total_line_counter = 0
		self.instructions = {}
		self.instruction_lookup = {}
		self.anti_dependencies = {}
		self.terminal_indecies = []
		self.path_weights = {}	# chain_index : pathweight
		self.scheduled = []

	def add_instruction(self, raw_instruction):
		# [inst_f, late, type]
		inst_info = self.parser.parse_instruction(raw_instruction, self.inst_counter)
		new_instruction = Instruction_t(inst_info[0], self.inst_counter, inst_info[1], inst_info[2])
		if new_instruction.is_leaf():
			self.instructions.update({self.total_line_counter : new_instruction})
			self.path_weights.update( {self.total_line_counter : new_instruction.get_latency()})
			# self.path_weights.append(new_instruction.get_latency())
			#self.instruction_lookup.update({new_instruction.instruction_number : [self.total_line_counter]})
			self.parser.update_registers(new_instruction.get_writable(), [self.total_line_counter])
			self.total_line_counter+=1 # THIS MUST BE THE LAST LINE
		else:
			chain_keys = self.parser.find_branches(new_instruction.get_instruction())
			#self.instruction_lookup.update({new_instruction.instruction_number : chain_keys})
			for key in chain_keys:
				pointer = self.instructions[key]
				prev = None
				while(pointer.next is not None):
					if(prev is not None and pointer.instruction == prev.instruction):
						break
					prev = pointer
					pointer = pointer.next

				self.path_weights[key]+=new_instruction.get_latency()

				pointer.next = new_instruction
				pointer = pointer.next
				if new_instruction.type != "io":
					writable = new_instruction.get_writable()
					self.parser.update_registers(writable, chain_keys)
				else:
					for i in chain_keys:
						if i != key:
							self.path_weights[i] += new_instruction.get_latency()
					break
		# exiting statements
		self.parser.find_potential_anti(new_instruction.instruction, new_instruction.instruction_number)
		self.inst_counter+=1

	def decide_lookup(self):
		# ptr = self.instructions[1]
		# while ptr is not None:
		# 	print(f"{ptr.instruction} @ {ptr.instruction_number}")
		# 	if ptr.instruction_number in self.instruction_lookup:
		# 		self.instruction_lookup[ptr.instruction_number].append(1)
		# 	else:
		# 		self.instruction_lookup.update({ptr.instruction_number : [1]})
		# 	ptr = ptr.next
		for chain_index, chain in self.instructions.items():
			ptr = chain
			while ptr is not None:
				if ptr.instruction_number in self.instruction_lookup:
					self.instruction_lookup[ptr.instruction_number].append(chain_index)
				else:
					self.instruction_lookup.update({ptr.instruction_number : [chain_index]})
				ptr = ptr.next


	def find_anti_dependence(self):
		self.decide_lookup()		
		# print(self.instruction_lookup)
		# print(self.parser.potential_dependencies)	
		for key,chain in self.instructions.items():
			ptr = chain
			while(ptr is not None):

				if ptr.instruction in self.parser.potential_dependencies and ptr.instruction_number == self.parser.potential_dependencies[ptr.instruction][1]:
					dep_info = self.parser.potential_dependencies[ptr.instruction]
					ptr_inst = ptr.instruction
					ptr_numb = ptr.instruction_number
					ptr_chain = key
					dep_inst = dep_info[0]
					dep_numb = dep_info[2]
					dep_chain = self.instruction_lookup[dep_numb]
					if ptr_chain not in dep_chain:
						# print(f"ptr: {ptr_inst} @ {ptr_numb} in chain {ptr_chain}")
						# print(f"dep: {dep_inst} @ {dep_numb} in chain {dep_chain}")
						# print("WE ADDED")
						if ptr_inst not in self.anti_dependencies:
							dep_info.append(dep_chain)
							self.anti_dependencies.update({ptr.instruction : dep_info})

				ptr = ptr.next
		# self.find_weights()
		print(self.anti_dependencies)
		self.adjust_path_weights()

	def adjust_path_weights(self):
		for inst, dep_info in self.anti_dependencies.items():
			print(f"inst: {inst} with {dep_info}")
			lhs_inst = inst 
			lhs_numb = dep_info[1]
			lhs_chain = self.instruction_lookup[lhs_numb]
			lhs_weight = self.get_weight_latency(lhs_chain[0], lhs_numb)
			dep_inst = dep_info[0]
			dep_numb = dep_info[2]
			dep_chain = dep_info[3]
			dep_weight = self.get_weight_latency(dep_chain[0], dep_numb)
			if lhs_weight[0] < dep_weight[0]:
				fix_value = dep_weight[0] - lhs_weight[0]
				ptr = self.instructions[lhs_chain[0]]
				while ptr is not None:
					if ptr.instruction_number == lhs_numb:
						ptr.fix_latency = fix_value+lhs_weight[1]
						print(f"adjusted {lhs_inst} @chain {lhs_chain} number {lhs_numb}")
						break
					ptr = ptr.next
	def get_weight_latency(self, chain, numb):
		ptr = self.instructions[chain]
		weight = 0
		good_to_go = False
		late = 0
		while ptr is not None:
			if ptr.instruction_number == numb:
				late = ptr.get_latency()
				good_to_go = True
			if good_to_go:
				weight+=ptr.get_latency()
			ptr = ptr.next
		return [weight,late]

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




