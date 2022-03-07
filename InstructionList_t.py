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
		self.instruction_lookup = {} # {inst_num : chain}?
		self.anti_dependencies = {}
		self.terminal_indecies = []
		self.path_weights = {}	# chain_index : pathweight
		self.occurence_list = {}
		self.all_output_chains = []
		self.previous_output = []
		self.anti_dependent_chains = {}

	def add_instruction(self, raw_instruction):
		# [inst_f, late, type]
		inst_info = self.parser.parse_instruction(raw_instruction, self.inst_counter)
		new_instruction = Instruction_t(inst_info[0], self.inst_counter, inst_info[1], inst_info[2])
		if new_instruction.is_leaf():
			self.instructions.update({self.total_line_counter : new_instruction})
			self.path_weights.update( {self.total_line_counter : new_instruction.get_latency()})
			self.parser.update_registers(new_instruction.get_writable(), [self.total_line_counter])
			self.total_line_counter+=1 # THIS MUST BE THE LAST LINE
		else:
			chain_keys = self.parser.find_branches(new_instruction.get_instruction())
			self.io_check(chain_keys, new_instruction)
			if new_instruction.type == "io":
				print(f"chain_keys: {chain_keys} for instructions {new_instruction.instruction_number}")
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

				is_output = self.output_check(new_instruction, key, chain_keys)
		# exiting statements
		self.parser.find_potential_anti(new_instruction.instruction, new_instruction.instruction_number)
		self.inst_counter+=1

	def io_check(self, chain_keys, new_instruction):
		if new_instruction.type=="io" and self.previous_output:
			v = self.previous_output.pop(0)
			if v not in chain_keys:
				#print(f"trying to add instructions {new_instruction.instruction_number} to chain {v}")
				chain_keys.append(v)


	def output_check(self, new_instruction, main_chain, chain_keys):
		if new_instruction.type != "io":
			writable = new_instruction.get_writable()
			self.parser.update_registers(writable, chain_keys)
		elif new_instruction.type == "io":

			if main_chain not in self.previous_output:
				self.previous_output.append(main_chain)
			if main_chain not in self.all_output_chains:
				arr = []
				for i in self.all_output_chains:
					if i not in chain_keys:
						arr.append(i)
				for i in arr:
					if i != main_chain:
						self.path_weights[i] += 1
						
				self.all_output_chains.append(main_chain)
				print(f"other indecies that need to be fixed: {arr}")
			#print(f"--all outputchains: {self.all_output_chains}")
			return True
		return False



	def get_next_chain(self, ready):
		# list_of_chain_indecies = []
		highest_weight_index = max(self.path_weights, key=self.path_weights.get)
		highest_weight = self.path_weights[highest_weight_index]

		if highest_weight_index not in ready:
			for index, weight in self.path_weights.items():
				if weight == highest_weight and index in ready:
						return index

		return highest_weight_index

	def get_occurence(self, inst_num):
		return self.occurence_list[inst_num]

	def decrease_weight(self, chain_index, modd):
		self.path_weights[chain_index]-=modd


	def converges_at(self, inst_numb):
		if len(self.instruction_lookup[inst_numb]) > 1:
			# print(f"Converges bc : {len(self.instruction_lookup[inst_numb])}")
			return True
		return False 

	def decide_lookup(self):
		for chain_index, chain in self.instructions.items():
			ptr = chain
			while ptr is not None:
				if ptr.instruction_number in self.instruction_lookup:
					self.instruction_lookup[ptr.instruction_number].append(chain_index)
				else:
					self.instruction_lookup.update({ptr.instruction_number : [chain_index]})

				if ptr.instruction_number in self.occurence_list:
					self.occurence_list[ptr.instruction_number]+=1
				else:
					self.occurence_list.update({ptr.instruction_number : 1})
				ptr = ptr.next

	def weight_test(self):
		print_statement = []
		path_weights = self.path_weights.copy()
		print(path_weights)
		for chain_index, chain in self.instructions.items():
			ptr = chain
			individual = []
			while(ptr is not None):
				w = path_weights[chain_index]
				individual.append(str(w))
				
				path_weights[chain_index]-=ptr.get_latency()
				ptr = ptr.next

			string = " --> ".join(individual)
			print_statement.append(string)
		for index,value in enumerate(print_statement):
			print(f"chain_index {index} : {value}")

	def find_anti_dependence(self):
		self.decide_lookup()
		#print(self.occurence_list)		
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
						if ptr_numb not in self.anti_dependencies:
							anti_info = [ptr_inst, ptr_chain, dep_inst, dep_chain, dep_numb]
							dep_info.append(dep_chain)
							self.anti_dependencies.update({ptr_numb : anti_info})
							if ptr_chain in self.anti_dependent_chains:
								print("we might have messed up in finding anti_dependencies")
							self.anti_dependent_chains.update({ptr_chain : dep_chain})
							# anti {bef_num : [bef_ins, bef_chain, aft_ins, aft_chain, aft_num]}
				ptr = ptr.next


	def anti_dependence_weight_fix(self):
		print(f"first time wights: {self.path_weights}")
		done_chains = []
		next_chain_count = 0
		while next_chain_count < len(self.instructions):
			if next_chain_count not in done_chains:
				self.adjust_path_weights(next_chain_count,[])	#start done_chains as []
			next_chain_count+=1
		highest_weight_index = max(self.path_weights, key=self.path_weights.get)
		highest_weight = self.path_weights[highest_weight_index]
		self.path_weights.update({0 : highest_weight+1})
		self.instructions[0].fix_latency = highest_weight
		#print()
		self.weight_test()
		#print()		

	# def a_adjust_path_weights(self, chain_index, done_chains):
	# 	if chain_index in done_chains:
	# 		return
	# 	if chain_index in self.anti_dependent_chains:
	# 		recurse_chain = self.anti_dependent_chains[chain_index]
	# 		self.adjust_path_weights(recurse_chain, done_chains)

	# 	pointer = self.instructions[chain_index]
	# 	chain_weight = 0
	# 	while pointer is not None:
	# 		ptr_inst_num = pointer.instruction_number
	# 		ptr_ins = ptr.instruction
	# 		if ptr_inst_num in self.anti_dependencies:
	# 			after = self.anti_dependencies[ptr_num]
	# 			after_ins = after[2]
	# 			after_chain = after[3][0]	# array of size one? always?
	# 			after_num = after[4]
	# 			after_weight = self.get_weight_latency(after_chain, after_num)
	# 			before_weight = self.get_weight_latency(chain_index, ptr_num)
	# 			if before_weight[0] < after_weight[0]:
	# 				fix_value = after_weight[0] - before_weight[0]
	# 				ptr.fix_latency = fix_value+before_weight[1]
	# 				update_chains = self.instruction_lookup[ptr_num]
	# 				# might be over counting
	# 				for i in update_chains:
	# 					self.path_weights[i]+=ptr.fix_latency
	# 		chain_weight += pointer.get_latency()

	# 		pointer = pointer.next


	def adjust_path_weights(self, chain_index, done_chains):
		if chain_index in done_chains:
			return
		done_chains.append(chain_index)

		ptr = self.instructions[chain_index]
		while ptr is not None:
			ptr_num = ptr.instruction_number
			ptr_ins = ptr.instruction
			#if it is an instruction that comes before something else
			if ptr_num in self.anti_dependencies:
				#print(f"{ptr_num} #{ptr_ins}# definitely has an anti dependence")
				after = self.anti_dependencies[ptr_num]
				after_ins = after[2]
				after_chain = after[3][0]	# array of size one? always?
				after_num = after[4]
				if self.are_unchecked_dependencies(after_num, after_chain):
					#print(f"{ptr_num} has more unchecked chains before processing; chain {after_chain} checked next")
					self.adjust_path_weights(after_chain, done_chains)
				after_weight = self.get_weight_latency(after_chain, after_num)
				before_weight = self.get_weight_latency(chain_index, ptr_num)
				if before_weight[0] < after_weight[0]:
					
					fix_value = after_weight[0] - before_weight[0]
					ptr.fix_latency = fix_value+before_weight[1]
					#print(f"{ptr_num} latency changed to {ptr.fix_latency}")
					update_chains = self.instruction_lookup[ptr_num]
					for i in update_chains:
						self.path_weights[i]+=ptr.fix_latency
			ptr = ptr.next


	def are_unchecked_dependencies(self, inst_num, inst_chain):
		#if after also has to come before another instruction
		if inst_num in self.anti_dependencies:
			return True
		#if this chain has an anti dependence at some point
		for anti_num, after_info in self.anti_dependencies.items():
			dep_chain = after_info[1] # chain that depends on something
			#print(f"our chain {inst_chain} == dep_chain {dep_chain} is {dep_chain == inst_chain}")
			if dep_chain == inst_chain:	# if target_chain actually depends on something else
				return True
		return False

	def can_continue(self):
		for key in self.path_weights:
			if self.path_weights[key] > 0:
				return True
		return False
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

	def print_instructions(self, optimal_path):
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
		#optimal_path.sort()
		print(f"optimal_path: {optimal_path}")
		print("------------------end------------------")




