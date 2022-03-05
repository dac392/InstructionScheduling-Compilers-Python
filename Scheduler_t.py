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
		
		#was_scheduled = []
		was_seen = {}	# {inst_num : times_seen}
		#pointers = [chain for chain_index,chain in IL.instructions.items()]
		cycle = 0
		ready = self.init_ready(IL) # {chain_index : chain}
		print(ready)
		active = {}	# {time : [chain, chain_index]}
		hold = {}	# {chain_index : chain}
		next_set = {} # {chain_index : chain}
		instruction = []
		last_inst_num = 0
		optimal_path = []
		while True:
			print(f"now cycle {cycle}")
			self.move_to_ready(cycle, active, ready)

			next_chain = IL.get_next_chain(ready)	# list_of_chains_w_highest_weight
			print(f"active: {active}")
			# print(f"chain List: {chain_list}")
			print(f"ig we decided on chain {next_chain}")
			print(f"cycle {cycle} next_chain {next_chain}")
			if next_chain in ready and not instruction:
				instruction.append(ready[next_chain].instruction)
				optimal_path.append(ready[next_chain].instruction_number)
			print(f"instruction: {instruction}")
			we_scheduled = False
			if next_chain in ready or next_chain in hold:
				# can_continue = IL.can_continue()
				self.move_to_hold(next_chain, ready, hold, was_seen)
				we_scheduled = self.move_to_active(next_chain, hold, was_seen, active, IL, cycle)
			if we_scheduled:
				self.scheduled_instructions.append(instruction.pop(0))
			print()
			if not IL.can_continue()or cycle > 32:
				print(f"finished in {cycle} cycles")
				IL.print_instructions(optimal_path)
				return cycle

			cycle+=1
		

	# active: groups all instances w the same time
	# active: {time : [chain, chain_index]}
	def move_to_ready(self, cycle, active, ready):
		if cycle in active:
			done_clusters = active.pop(cycle) # [ [chain, chain_index]...  ]
			print(f"popped nodes that finish at cycle {cycle}")
			print(f"nodes that i can move to ready : {done_clusters}")
			#inst_finished = [ node_info[0].instruction_number for node_info in done_clusters] # [ 1, 7, 1, 1, ...]
			for node in done_clusters:
				chain_index = node[1]
				chain = node[0]
				if chain.next is not None:
					if chain_index in ready:
						ready[chain_index].append(chain.next)
						print("I don't think that you're supposed to have more than one node from a chain at the same time")
					else:
						ready.update({chain_index : chain.next})
						print(f"moved{chain_index} into ready")
		else:
			print(f"could not move anything from active to ready")

		print(f"things in active: {active}")

		#ready:: {chain_index : next_node}

	def move_to_hold(self, next_chain, ready, hold, was_seen):
		
		if next_chain in ready or next_chain in hold:
			next_inst_num = ready[next_chain].instruction_number if next_chain in ready else hold[next_chain].instruction_number
		
		if next_chain in ready:# and IL.can_continue()
			actual_chain = ready.pop(next_chain)
			hold.update({next_chain : actual_chain})
			print(f"moved {next_chain} into hold")
			#print(f"hold: {hold}")
			if next_inst_num not in was_seen:
				was_seen.update({next_inst_num : 1})
			else:
				was_seen[next_inst_num]+=1

			other_pops = []
			for chain_index, chain in ready.items():
				if chain.instruction_number == next_inst_num:
					other_pops.append(chain_index)
			for index in other_pops:
				additional = ready.pop(index)
				hold.update({index : additional})
				print(f"moved {index} into hold")
				was_seen[next_inst_num]+=1
			print(hold)
		

	def move_to_active(self, next_chain, hold, was_seen, active, IL, cycle):
		next_inst_num = hold[next_chain].instruction_number
		if was_seen[next_inst_num] == IL.get_occurence(next_inst_num):
			chains_arr = [k for k in hold.keys()]
			
			for chain_index in chains_arr:
				hold_chain = hold.pop(chain_index)
				late = hold_chain.get_latency()
				done_time = cycle+late
				if done_time in active:
					active[done_time].append([hold_chain, chain_index])
				else:
					active.update({done_time : [[hold_chain, chain_index]]})
				#print(f"Trying to decrease index {chain_index} with mod {late}")
				print(f"moved {chain_index} into active")
				IL.decrease_weight(chain_index, late)
			return True
		return False


	def init_ready(self, IL):
		ready = {}
		for chain_index, chain in IL.instructions.items():
			ready.update({chain_index : chain})
		return ready
	def highest_latency(self):
		print("B")
	def my_own(self):
		print("C")
























