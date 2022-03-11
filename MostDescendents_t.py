class MostDescendents_t:
	def __init__(self, ready, IL):
		self.ready_instructions = self.init_ready_tracker(ready)		
		self.instruction_positions = self.init_ready_positions(ready)	
		self.ready_latencies = self.init_ready_latencies(ready)			
		self.anti_dependence = self.init_anti_dependence(IL)			
		
		# self.live_ranges = self.init_live_ranges(IL)					
		# self.lock = {}													
		# self.locked_chains = {}											

		self.descendents = self.init_descendents(IL)					
		self.ready_descendents = self.init_ready_descendents(ready)		
		self.merge_point_lookup = self.init_merge_point_lookup(IL)
		self.occurence_list = self.init_occurence_list(IL)
		self.scheduled_tracker = []


	# main functions
	def get_next_chain(self, ready, IL):
		if 1 in self.ready_instructions:
			return 0
		if not bool(ready):
			return -1

		highest_late = -1
		highest = -1
		highest_chain = -1
		for chain_index, chain in ready.items():
			instruction = chain.instruction_number
			if self.occurence_list[instruction] == 1 or (self.occurence_list[instruction] > 1 and self.ready_instructions[instruction] == 2):
				if instruction in self.anti_dependence and self.anti_dependence[instruction] not in self.scheduled_tracker: # instruction has to come before something else
					continue
				if highest < self.ready_descendents[chain_index]:
					highest_chain = chain_index
					highest = self.ready_descendents[chain_index]


		return highest_chain

	def move_to_active(self, cycle, next_chain, ready, active, IL):
		ready_instruction = ready.pop(next_chain)
		instruction = ready_instruction.instruction_number
		formated = ready_instruction.instruction
		self.remove_additional_instruction(ready, instruction)
		done_cycle = cycle+self.ready_latencies[instruction]
		if done_cycle not in active:
			active.update({done_cycle : [[ready_instruction, next_chain]] })
		else:
			active[done_cycle].append( [ready_instruction, next_chain] )

		self.ready_instructions.pop(instruction)
		self.instruction_positions.pop(instruction) # idk what this is but maybe check it, cause i feel like we might not be popping as much as we have to
		self.scheduled_tracker.append(instruction)
		self.ready_descendents.pop(next_chain)
		# print()

		return ready_instruction.instruction
	def move_to_ready(self, cycle, active, ready):
		if cycle in active:
			active_instruct_clusters = active.pop(cycle)
			for cluster in active_instruct_clusters:
				chain = cluster[0].next
				if chain is None:
					continue
				chain_index = cluster[1]
				instruction = chain.instruction_number
				if self.can_be_made_ready(instruction, chain_index):
					late = chain.get_latency()
					ready.update({chain_index : chain})
					self.instruction_positions.update({instruction : [chain_index]})
					if instruction not in self.ready_instructions:
						self.ready_instructions.update({instruction : 1})
						self.ready_latencies.update({instruction : late})

					else:
						self.ready_instructions[instruction]+=1
					self.ready_descendents.update({chain_index : self.descendents[chain_index]})


	def can_be_made_ready(self, instruction, chain_index):
		total_occurence = self.occurence_list[instruction]
		# if chain_index not in self.
		if instruction in self.scheduled_tracker:
			return False

		if chain_index not in self.merge_point_lookup[instruction]:
			return False

		if total_occurence == 1 and instruction not in self.ready_instructions:
			# instruction hasn't been scheduled and there is only one of this instructino, then sure
			return True
		if total_occurence > 1 and (instruction not in self.ready_instructions or self.ready_instructions[instruction] < 2):
			# if it isn't in scheduled then it either hasn't been seen or there is at least one.
			# but must only be able to add at most 2 of the same instruction
			return True
		
		return False

	def remove_additional_instruction(self, ready, instruction):
		if self.occurence_list[instruction] > 1:
			posible_chains = self.merge_point_lookup[instruction]
			# posible_chains = self.instruction_positions[instruction]
			for chain_index in posible_chains:
				if chain_index in ready:
					ready.pop(chain_index)
					self.ready_descendents.pop(chain_index)
					self.descendents.pop(chain_index)	# we'll see about this one

	def has_finished(self, ready, active):
		if not bool(ready) and not bool(active):
			return True
		return False



	# init statements
	def init_live_ranges(self, IL):
		state = {}
		seen = []
		for index, chain in IL.instructions.items():
			in_this_chain = []
			ptr = chain
			local = {}
			while ptr is not None:
				inst = ptr.instruction_number
				formated = ptr.instruction
				if inst in seen:
					break
				seen.append(inst)
				read = IL.parser.get_readable(formated)
				write = IL.parser.get_writable(formated)
				for readable in read:
					if readable != -1:
						if readable in local:
							previous = local.pop(readable)
							local.update({readable : [previous[0],inst]})
						# else:
						# 	local.update({readable : [inst, inst]})
				if write != -1:
					if write in local and write in state:
						previous = local.pop(write)
						if previous not in state[write]:
							state[write].append(previous)
						
					elif write in local:	# only if its not already there
						previous = local.pop(write)
						state.update({write : [ previous ] })
						
					local.update({write : [inst, inst]})
				ptr = ptr.next
			for key, value in local.items():
				if key in state:
					if value not in state[key]:
						state[key].append(value)
				else:
					state.update({key : [value] })
		#print(f"live ranges: {state}")
		return state

	def init_descendents(self, IL):
		state = {}
		for chain_index, chain in IL.instructions.items():
			ptr = chain
			while ptr is not None:
				if chain_index not in state:
					state.update({chain_index : 1})
				else:
					state[chain_index]+=1
				ptr = ptr.next

		return state

	def init_merge_point_lookup(self, IL):
		state = {}
		for chain_index, chain in IL.instructions.items():
			ptr = chain
			while ptr is not None:
				instruction = ptr.instruction_number
				if instruction not in state:
					state.update({instruction : [chain_index]})
				else:
					state[instruction].append(chain_index)
					break
				ptr = ptr.next
		return state

	def init_ready_descendents(self, ready):
		state = {}
		for chain_index, chain in ready.items():
			state.update({chain_index : self.descendents[chain_index]})
		return state

	def init_ready_tracker(self, ready):
		state ={}
		for chain_index, chain in ready.items():
			if chain.instruction_number not in state:
				state.update({chain.instruction_number : 1})
			else:
				state[chain.instruction_number]+=1 # shouldn't happen... but just in case
		return state


	def init_anti_dependence(self, IL):
		# IL: {ptr_num : [ptr_inst, ptr_chain, dep_inst, dep_chain, dep_numb]}
		state = {} # {after : before}
		for instruction, cluster in IL.anti_dependencies.items():
			before = instruction
			after = cluster[4]
			state.update({after : before}) # i have no clue if you might have more than one after
		return state

	def init_occurence_list(self, IL):
		# state = IL.occurence_list.copy()
		state = {}
		for chain_index, chain in IL.instructions.items():
			ptr = chain
			while ptr is not None:
				instruction = ptr.instruction_number
				if instruction not in state:
					state.update({instruction : 1})
				else:
					state[instruction]+=1
					break
				ptr = ptr.next
		return state
	def init_ready_latencies(self, ready):
		state = {} # {inst: late}
		for chain_index, chain in ready.items():
			inst = chain.instruction_number
			if inst not in state:
				state.update({inst : chain.get_latency()})
		return state
	def init_ready_positions(self, ready):
		state = {}
		for chain_index, chain in ready.items():
			instruction = chain.instruction_number
			if instruction not in state:
				state.update({instruction : [chain_index]})
			else:	# actually, this might never happen at init
				state[instruction].append(chain_index)
		return state
	def find_anti_dependence(self, IL):
		preliminary = self.preliminary_dependencies(IL)	#[ {instruction : id} {} ...]
		#print(preliminary)
		for index, entire_chain in enumerate(preliminary):
			if index+1 == len(preliminary):
				break
			for j_index, j_chain in enumerate(preliminary, start=index+1):
				#least_length = len(entire_chain) if len(entire_chain) < len(j_chain) else: len(j_chain)
				j_vals = list(j_chain.values())
				# print(j_vals)
				j_writes = [IL.parser.get_writable(j) for j in j_vals]
				for instruction, str_inst in entire_chain.items():
					main_read = IL.parser.get_readable(str_inst)
					for i,j in enumerate(j_writes):
						if main_read == j:
							if instruction not in IL.anti_dependencies:
								IL.anti_dependencies.update({instruction : [j_vals[i]]  })
							else:
								IL.anti_dependencies[instruction].append(j_vals[i])
		# print(IL.anti_dependencies)

	def preliminary_dependencies(self, IL):
		seen_list = []
		dependencies = []
		for chain_index, chain in IL.instructions.items():
			ptr = chain
			dep = {}
			while ptr is not None:
				inst_num = ptr.instruction_number
				if inst_num not in seen_list:
					seen_list.append(inst_num)
					dep.update({inst_num : ptr.instruction})
				else:
					break
				ptr = ptr.next
			dependencies.append(dep)
		return dependencies


