class Heuristics_t:
	def __init__(self, ready, IL):
		self.ready_instructions = self.init_ready_tracker(ready)		# {instruction : count}
			# ^ make sure that you only add at most 2 chains with the same instruction number.
			#	all other additional chains should just terminate
		self.instruction_positions = self.init_ready_positions(ready)	# {instruction : [chain]}
		self.ready_latencies = self.init_ready_latencies(ready)			# {instruction : latency}
		
		self.most_descendents = {}										# {chain : descendent_count}
		self.ready_descendent_tracker = {}								# {chain : descendent_count}
		self.merge_point_lookup = {}	# theory crafting
		self.second_heuristic = False
		# should never be touched
		self.anti_dependence = self.init_anti_dependence(IL)			# {after : before}
		self.occurence_list = self.init_occurence_list(IL)				# {instruction : count}
		self.scheduled_tracker = []



	# HighestLatency
	def get_next_highest_latency_instruction(self, ready):
		if 1 in self.ready_instructions:
			return 0

		highest = 0
		highest_chain = -1
		for chain_index, chain in ready.items():
			instruction = chain.instruction_number
			if instruction in self.anti_dependence and self.anti_dependence[instruction] not in self.scheduled_tracker: # instruction has to come before something else
				# if instruction must come after something else
				# and before has already been scheduled, then you can use this instruction
				#print(f"instruction {instruction} comes after something that hasn't been scheduled yet")
				continue
			if self.occurence_list[instruction] > 1 and self.ready_instructions[instruction] != 2:
				# will only be true if you have exactly 2 of this instruction in ready
				#print(f"instruction {instruction} is a merge point and there are only {self.ready_instructions[instruction]} instances in ready")
				continue
			if instruction in self.scheduled_tracker:
				print(f"Warning, instruction {instruction} should not be in ready anymore, it was already processed. we messed up")
				continue

			if self.ready_latencies[instruction] > highest:
				highest = self.ready_latencies[instruction]
				highest_chain = chain_index

		return highest_chain

	def move_to_active(self, cycle, next_chain, ready, active):
		ready_instruction = ready.pop(next_chain)
		instruction = ready_instruction.instruction_number
		self.remove_additional_instruction(ready, instruction)
		done_cycle = cycle+self.ready_latencies[instruction]
		if done_cycle not in active:
			active.update({done_cycle : [[ready_instruction, next_chain]]})
		else:
			active[done_cycle].append( [ready_instruction, next_chain] )

		self.ready_instructions.pop(instruction)
		self.instruction_positions.pop(instruction)
		self.ready_latencies.pop(instruction)
		self.scheduled_tracker.append(instruction)
		if self.second_heuristic:
			# self.most_descendents[next_chain]-=1
			self.ready_descendent_tracker.pop(next_chain)
			# self.merge_point_lookup.pop(instruction)	we'll see about this

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

					if self.second_heuristic:
						self.ready_descendent_tracker.update({chain_index : self.most_descendents[chain_index]})


	def can_be_made_ready(self, instruction, chain_index):
		total_occurence = self.occurence_list[instruction]
		if instruction in self.scheduled_tracker:
			return False

		if self.second_heuristic and chain_index not in self.merge_point_lookup[instruction]:
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
			posible_chains = None
			if self.second_heuristic:
				posible_chains = self.merge_point_lookup[instruction]
			else:
				posible_chains = self.instruction_positions[instruction]
			for chain_index in posible_chains:
				if chain_index in ready:
					ready.pop(chain_index)
					if self.second_heuristic:
						self.ready_descendent_tracker.pop(chain_index)
						self.most_descendents.pop(chain_index)	# we'll see about this one

	def has_finished(self, ready, active):
		if not bool(ready) and not bool(active):
			return True
		return False



	# Most Successors
	def init_most_descendents(self, IL, ready):
		self.second_heuristic = True
		for chain_index, chain in IL.instructions.items():
			ptr = chain
			while ptr is not None:
				if chain_index not in self.most_descendents:
					self.most_descendents.update({chain_index : 1})
				else:
					self.most_descendents[chain_index]+=1
				ptr = ptr.next
		self.init_ready_descendents(ready)
		self.init_merge_point_lookup(IL)

	def init_ready_descendents(self, ready):
		for chain_index, chain in ready.items():
			self.ready_descendent_tracker.update({chain_index : self.most_descendents[chain_index]})

	def init_merge_point_lookup(self, IL):
		for chain_index, chain in IL.instructions.items():
			ptr = chain
			while ptr is not None:
				instruction = ptr.instruction_number
				if instruction not in self.merge_point_lookup:
					self.merge_point_lookup.update({instruction : [chain_index]})
				else:
					self.merge_point_lookup[instruction].append(chain_index)
					break
				ptr = ptr.next

	def find_highest_descendent_chain(self):
		keys = list(self.ready_descendent_tracker.keys())
		keys.sort()
		highest = 0
		highest_chain = -1
		for k in keys:
			v = self.ready_descendent_tracker[k]
			if v > highest:
				highest = v
				highest_chain = k
		return highest_chain

	def get_highest_descendent(self, ready):
		if 1 in self.ready_instructions:
			return 0
		if not bool(ready):	# empty
			return -1
		#highest_chain = max(self.ready_descendent_tracker, key=self.ready_descendent_tracker.get)
		highest_chain = self.find_highest_descendent_chain()
		instruction = ready[highest_chain].instruction_number
		# print(f"in theory it should be {highest_chain}")
		if instruction in self.anti_dependence and self.anti_dependence[instruction] in self.scheduled_tracker:
			return highest_chain
		if self.occurence_list[instruction] == 1 or (self.occurence_list[instruction]>1 and self.ready_instructions[instruction] > 1):
			return highest_chain

		# if self.occurence_list[instruction] > 1 and self.ready_instructions[instruction] != 2:
		# 	merge_list = self.merge_point_lookup[instruction]
		# 	for c in merge_list:
		# 		if c != highest_chain and c in self.ready_descendent_tracker:
		# 			return c
		highest = 0
		highest_chain = -1
		for chain_index, chain in ready.items():
			instruction = chain.instruction_number
			if instruction in self.anti_dependence and self.anti_dependence[instruction] not in self.scheduled_tracker: # instruction has to come before something else
				# potential optimization, return the chain in which before is @
				continue
			if self.occurence_list[instruction] > 1 and self.ready_instructions[instruction] != 2:
				continue
			if instruction in self.scheduled_tracker:
				print(f"Warning, instruction {instruction} should not be in ready anymore, it was already processed. we messed up")
				continue

			if self.ready_descendent_tracker[chain_index] > highest:
				highest = self.ready_descendent_tracker[chain_index]
				highest_chain = chain_index

		return highest_chain



	# utility and set up:
	def init_ready_tracker(self, ready):
		state ={}
		for chain_index, chain in ready.items():
			if chain.instruction_number not in state:
				state.update({chain.instruction_number : 1})
			else:
				state[chain.instruction_number]+=1 # shouldn't happen... but just in case
		return state
	def init_ready_latencies(self, ready):
		state = {} # {inst: late}
		for chain_index, chain in ready.items():
			inst = chain.instruction_number
			if inst not in state:
				state.update({inst : chain.get_latency()})
		return state
	def init_anti_dependence(self, IL):
		# IL: {ptr_num : [ptr_inst, ptr_chain, dep_inst, dep_chain, dep_numb]}
		state = {} # {after : before}
		for instruction, cluster in IL.anti_dependencies.items():
			before = instruction
			after = cluster[4]
			state.update({after : before}) # i have no clue if you might have more than one after
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

		# print(f"occurences: {state}")
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
				print(j_vals)
				j_writes = [IL.parser.get_writable(j) for j in j_vals]
				for instruction, str_inst in entire_chain.items():
					main_read = IL.parser.get_readable(str_inst)
					for i,j in enumerate(j_writes):
						if main_read == j:
							if instruction not in IL.anti_dependencies:
								IL.anti_dependencies.update({instruction : [j_vals[i]]  })
							else:
								IL.anti_dependencies[instruction].append(j_vals[i])
		print(IL.anti_dependencies)

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












