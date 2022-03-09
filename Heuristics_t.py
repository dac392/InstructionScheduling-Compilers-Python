class HighestLatency_t:
	def __init__(self, ready, IL):
		self.ready_instructions = self.init_ready_tracker(ready)		# {instruction : count}
			# ^ make sure that you only add at most 2 chains with the same instruction number.
			#	all other additional chains should just terminate
		self.instruction_positions = self.init_ready_positions(ready)	# {instruction : [chain]}
		self.ready_latencies = self.init_ready_latencies(ready)			# {instruction : latency}
		
		# should never be touched
		self.anti_dependence = self.init_anti_dependence(IL)			# {after : before}
		self.occurence_list = self.init_occurence_list(IL)				# {instruction : count}
		self.scheduled_tracker = []
		# self.total_feasible_chain = len(IL.instructions) - 1 probably not needed



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
				if self.can_be_made_ready(instruction):
					late = chain.get_latency()
					ready.update({chain_index : chain})
					self.instruction_positions.update({instruction : [chain_index]})
					if instruction not in self.ready_instructions:
						self.ready_instructions.update({instruction : 1})
						self.ready_latencies.update({instruction : late})
					else:
						self.ready_instructions[instruction]+=1


	def can_be_made_ready(self, instruction):
		total_occurence = self.occurence_list[instruction]
		if instruction in self.scheduled_tracker:
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
			#print(self.instruction_positions)
			posible_chains = self.instruction_positions[instruction]
			for chain_index in posible_chains:
				if chain_index in ready:
					ready.pop(chain_index)


	def has_finished(self, ready, active):
		if not bool(ready) and not bool(active):
			return True
		return False

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














