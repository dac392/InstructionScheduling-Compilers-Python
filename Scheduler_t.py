from InstructionList_t import InstructionList_t
from Heuristics_t import Heuristics_t
class Scheduler_t:
	def __init__ (self, mode, instructions):
		self.mode = mode
		self.raw_instructions = instructions
		self.scheduled_instructions = []


	def schedule(self):
		execute = {"-a":self.longest_latency, "-b":self.highest_latency, "-c":self.highest_descendent};
		statement = execute[self.mode]()
		return statement

	def longest_latency(self):
		IL = InstructionList_t()
		for line in self.raw_instructions:
			IL.add_instruction(line)
		IL.find_anti_dependence()
		IL.anti_dependence_weight_fix();
		# IL.print_instructions([])
		# IL.weight_test()

		was_seen = {}	# {inst_num : times_seen}
		cycle = 0
		ready = self.init_ready(IL) # {chain_index : chain}
		active = {}	# {time : [chain, chain_index]}
		hold = {}	# {chain_index : chain}
		instruction = []
		optimal_path = []
		while True:
			self.move_to_ready(cycle, active, ready,IL)
			next_chain = IL.get_next_chain(ready)	# list_of_chains_w_highest_weight
			if next_chain in ready and not instruction:
				instruction.append(ready[next_chain].instruction)
				optimal_path.append(ready[next_chain].instruction_number)
			we_scheduled = False
			if next_chain in ready or next_chain in hold:
				self.move_to_hold(next_chain, ready, hold, was_seen,IL)
				we_scheduled = self.move_to_active(next_chain, hold, was_seen, active, IL, cycle)
			if we_scheduled:
				self.scheduled_instructions.append(instruction.pop(0))
			if not IL.can_continue():
				return cycle

			cycle+=1
		

	# active: groups all instances w the same time
	# active: {time : [chain, chain_index]}
	def move_to_ready(self, cycle, active, ready, IL):
		if cycle in active:
			done_clusters = active.pop(cycle) # [ [chain, chain_index]...  ]
			# inst_finished = [ node_info[0].instruction_number for node_info in done_clusters] # [ 1, 7, 1, 1, ...]
			for node in done_clusters:
				chain_index = node[1]
				chain = node[0]
				if chain.next is not None:
					ready.update({chain_index : chain.next})
					#print(f"moved {chain_index} into ready")
		#ready:: {chain_index : next_node}

	def move_to_hold(self, next_chain, ready, hold, was_seen,IL):
		next_inst_num = ready[next_chain].instruction_number if next_chain in ready else hold[next_chain].instruction_number
		if next_chain in ready:
			actual_chain = ready.pop(next_chain)
			hold.update({next_chain : actual_chain})
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
				was_seen[next_inst_num]+=1
		
		

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
				IL.decrease_weight(chain_index, late)
			return True
		return False


	def init_ready(self, IL):
		ready = {}
		for chain_index, chain in IL.instructions.items():
			ready.update({chain_index : chain})
		return ready

	def highest_latency(self):
		IL = InstructionList_t()
		for line in self.raw_instructions:
			IL.add_instruction(line)
		IL.find_anti_dependence()
		IL.anti_dependence_weight_fix();

		cycle = 0
		ready = self.init_ready(IL) # {chain_index : chain}
		HL_t = Heuristics_t(ready,IL)
		active = {}	# {time : [chain, chain_index]}

		while True:
			HL_t.move_to_ready(cycle, active, ready)
			next_chain = HL_t.get_next_highest_latency_instruction(ready)
			if next_chain > -1:
				scheduled = HL_t.move_to_active(cycle, next_chain, ready, active)
				self.scheduled_instructions.append(scheduled)
			
			if  HL_t.has_finished(ready, active):
				return cycle+1
			cycle += 1

	# should try to better compile time
	def highest_descendent(self):
		IL = InstructionList_t()
		for line in self.raw_instructions:
			IL.add_instruction(line)
		IL.find_anti_dependence()
		IL.anti_dependence_weight_fix();

		cycle = 0
		ready = self.init_ready(IL) # {chain_index : chain}
		active = {}	# {time : [chain, chain_index]}
		MD_t = Heuristics_t(ready,IL)
		MD_t.init_most_descendents(IL, ready)

		while True:
			#print(f"cycle: {cycle}")
			MD_t.move_to_ready(cycle, active, ready)
			next_chain = MD_t.get_highest_descendent(ready)
			#print(f"chain that we setled on: {next_chain}\n")
			if next_chain > -1:
				scheduled = MD_t.move_to_active(cycle, next_chain, ready, active)
				self.scheduled_instructions.append(scheduled)
			
			if  MD_t.has_finished(ready, active):
				#print(f"occurences: {MD_t.occurence_list}")
				#print(f"path: {MD_t.scheduled_tracker}")
				return cycle+1
			cycle += 1
























