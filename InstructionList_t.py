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
		self.anti_dependencies = {}		# {ptr_num : [ptr_inst, ptr_chain, dep_inst, dep_chain, dep_numb]}
		self.terminal_indecies = []
		self.path_weights = {}	# chain_index : pathweight
		self.occurence_list = {}
		self.all_output_chains = []
		self.previous_output = []
		self.anti_dependent_chains = {}
		self.chain_tracker = {}

	def get_instructino_branch(self, new_instruction):
		all_chains = self.parser.find_branches(new_instruction.get_instruction())
		inst_num = new_instruction.instruction_number
		# Single instruction:
		if len(all_chains) == 1:
			self.chain_tracker.update({all_chains[0] : all_chains[0]})
			self.instruction_lookup.update({inst_num : all_chains[0]})
			return all_chains

		# More than one. Must return list of size 2
		#print(f"all chains: {all_chains}")
		#print(f"chain_tracker: {self.chain_tracker}")
		state = []
		merge_point = all_chains[0]
		for i in all_chains:
			# if i not in self.chain_tracker:

			chain_index = self.chain_tracker[i]
			if chain_index not in state:
				state.append(chain_index)
		for i in all_chains:
			self.chain_tracker.update({i : merge_point})
			
		self.instruction_lookup.update({inst_num : merge_point})
		return state


	def add_instruction(self, raw_instruction):
		# [inst_f, late, type]
		inst_info = self.parser.parse_instruction(raw_instruction, self.inst_counter)
		new_instruction = Instruction_t(inst_info[0], self.inst_counter, inst_info[1], inst_info[2])
		if new_instruction.is_leaf():
			self.instructions.update({self.total_line_counter : new_instruction})
			self.path_weights.update( {self.total_line_counter : new_instruction.get_latency()})
			self.parser.update_registers(new_instruction.get_writable(), [self.total_line_counter])
			self.instruction_lookup.update({new_instruction.instruction_number : self.total_line_counter})
			self.chain_tracker.update({self.total_line_counter : self.total_line_counter})
			self.total_line_counter+=1 # THIS MUST BE THE LAST LINE
		else:
			chain_keys = self.get_instructino_branch(new_instruction)
			self.io_check(chain_keys, new_instruction)

			#if new_instruction.type == "io":
			#print(f"chain_keys: {chain_keys} for instructions {new_instruction.instruction_number}")
			for key in chain_keys:
				pointer = self.instructions[key]
				while pointer.next is not None:
					pointer = pointer.next
				# print(f"currently adding instruction {new_instruction.instruction_number} to chain {key}")
				self.path_weights[key]+=new_instruction.get_latency()
				pointer.next = new_instruction
				# pointer = pointer.next

				is_output = self.output_check(new_instruction, key, chain_keys)
				# self.print_instructions([])
		# exiting statements
		#print()
		
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
				# print(f"other indecies that need to be fixed: {arr}")

			# print(f"--all outputchains: {self.all_output_chains}")
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
			# print(f"chain_index: {chain_index}")
			ptr = chain
			while ptr is not None:
				if ptr.instruction_number in self.instruction_lookup:
					v = self.instruction_lookup[ptr.instruction_number]
					if chain_index not in v:
						self.instruction_lookup[ptr.instruction_number].append(chain_index)
				else:
					self.instruction_lookup.update({ptr.instruction_number : [chain_index]})

				if ptr.instruction_number in self.occurence_list:
					self.occurence_list[ptr.instruction_number]+=1
				else:
					self.occurence_list.update({ptr.instruction_number : 1})
				ptr = ptr.next
				# print(f"instruction_lookup: {self.instruction_lookup}")
				# print(f"occurence_list: {self.occurence_list}")

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
		#print(f"look up: {self.instruction_lookup}")
		# print(f"potential_dependencies: {self.parser.potential_dependencies}")
		#self.decide_lookup()		
		for key,chain in self.instructions.items():
			ptr = chain
			while(ptr is not None):
				self.count_occurence(ptr.instruction_number)
				if self.is_anti_dependent(ptr.instruction, ptr.instruction_number):
					dep_info = self.parser.potential_dependencies[ptr.instruction]
					ptr_inst = ptr.instruction
					ptr_numb = ptr.instruction_number
					ptr_chain = key
					dep_inst = dep_info[0]
					dep_numb = dep_info[2]
					dep_chain = self.instruction_lookup[dep_numb]
					anti_info = [ptr_inst, ptr_chain, dep_inst, dep_chain, dep_numb]
					self.anti_dependencies.update({ptr_numb : anti_info})
					self.anti_dependent_chains.update({ptr_chain : dep_chain})
				ptr = ptr.next	
		#print(f"occurence_list: {self.occurence_list}")

	def is_anti_dependent(self, bef_inst, bef_num):
		if bef_inst in self.parser.potential_dependencies and bef_num == self.parser.potential_dependencies[bef_inst][1]:
			aft_num = self.parser.potential_dependencies[bef_inst][2]
			if self.instruction_lookup[bef_num] != self.instruction_lookup[aft_num]:
				return True
		return False
	def count_occurence(self, inst_num):
		if inst_num in self.occurence_list:
			self.occurence_list[inst_num]+=1
		else:
			self.occurence_list.update({inst_num : 1})


	def resolve_anti_weight(self, inst_chain, done):

		if inst_chain in done:
			return 0

		done.append(inst_chain)
		ptr = self.instructions[inst_chain]
		weight = 0
		while ptr is not None:
			ptr_inst = ptr.instruction
			ptr_num = ptr.instruction_number
			if ptr_num in self.anti_dependencies:
				aft_info = self.anti_dependencies[ptr_num]
				aft_chain = aft_info[3]
				aft_num = aft_info[4]
				if aft_num in self.anti_dependencies or aft_chain in self.anti_dependent_chains:
					self.resolve_anti_weight(aft_chain, done)

				after_weight = self.get_weight_latency(aft_chain, aft_num)
				before_weight = self.get_weight_latency(inst_chain, ptr_num)
				if before_weight[0] < after_weight[0]:
					fix_value = after_weight[0] - before_weight[0]
					ptr.fix_latency = fix_value+before_weight[1]
					#print(f"{ptr_num} latency changed to {ptr.fix_latency}")
					update_chains = self.instruction_lookup[ptr_num]
					# for i in update_chains:
					# 	self.path_weights[i]+=ptr.fix_latency
			weight+= ptr.get_latency()
			ptr = ptr.next
		self.path_weights[inst_chain] = weight
		return weight

	def anti_dependence_weight_fix(self):
		# print(f"first time wights: {self.path_weights}")
		anti_bef = list(self.anti_dependent_chains.keys())
		anti_aft = list(self.anti_dependent_chains.values())
		safe_fix = [i for i in anti_aft if i not in anti_bef]	# chains w/o antidependence but are depended on
		for i in self.instructions.keys():
			if i not in safe_fix and i not in anti_bef:
				safe_fix.append(i)
		done = []
		for chain in safe_fix:
			ptr = self.instructions[chain]
			weight = 0
			while(ptr is not None):
				weight += ptr.get_latency()
				ptr = ptr.next
			self.path_weights[chain] = weight
			done.append(chain)

		for chain in anti_bef:
			if chain not in done:
				self.resolve_anti_weight(chain, done)
		highest_weight_index = max(self.path_weights, key=self.path_weights.get)
		highest_weight = self.path_weights[highest_weight_index]
		self.path_weights.update({0 : highest_weight+1})
		self.instructions[0].fix_latency = highest_weight	

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
				after_chain = after[3]
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
		print(f"path weights: {self.path_weights}")
		print(f"anti dependencies: {self.anti_dependencies}")
		#optimal_path.sort()
		print(f"optimal_path: {optimal_path}")
		print("------------------end------------------")




