class InstructionList:
	class Instruction:
		def __init__(self, instruction, latency, instruction_type, order_number):
			self.instruction = instruction
			self.order_number = order_number
			self.latency = latency	# weight
			self.fix_latency = -1
			self.has_been_fixed = False
			self.path_weight = 0
			self.type = instruction_type
			self.next =  None
		def get_main_instruction(self):
			return self.instruction.split(" ")[0]
		def get_full_instruction(self):
			return self.instruction.split(" ")
		def is_leaf(self):
			ins = self.get_main_instruction()
			if ins == "loadI":
				return True
			return False
		# returns the index of the register/memory being written to
		def get_writable(self):
			return self.instruction.split(" ")[3]
		# returns the index of the register/memoru being read from
		def get_readable(self):
			return self.instruction.split(" ")[1]



	def __init__(self):
		# self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[2, "arithmatic"], "div":[2, "arithmatic"]}
		# self.memory_latencies = {"load":[3,"load1"], "loadI":[1,"load2"],"loadAI":[3,"load2"], "store":[3,"memory"], "storeAI":[3,"memory"]}
		# self.io_latencies = {"outputAI":[1,"io"]}
		self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[3, "arithmatic"], "div":[3, "arithmatic"]}
		self.memory_latencies = {"load":[5,"load1"], "loadI":[1,"load2"],"loadAI":[5,"load2"], "store":[5,"memory"], "storeAI":[5,"memory"]}
		self.io_latencies = {"outputAI":[1,"io"]}
		self.register_lookup = {}
		self.instruction_counter = 0
		
		self.instructions = []
		self.path_weights = []
		self.scheduled = []



	# Because .append() alway adds to the end of a list, its not complicated
	# reminder: instruct_info = [instruction, latency, type]
	def add_instruction(self, instruct_info, order_number):
		node = self.Instruction(instruct_info[0], instruct_info[1], instruct_info[2], order_number)
		self.instruction_counter+=1
		io_index = -1
		if node.is_leaf():
			node.path_weight = node.latency
			self.instructions.append(node)
			self.register_lookup.update({ node.get_writable() : [len(self.instructions)-1] })
		else:
			branch_index = None
			readable = node.get_readable()
			try:
				branch_index = self.register_lookup[readable]
			except KeyError:
				branch_index = self.get_read_indecies(readable)
			for index in branch_index:
				pointer = self.instructions[index]
				prev = None
				while(pointer.next):
					pointer.path_weight += node.latency
					if(prev is not None and pointer.instruction == prev.instruction):
						break
					prev = pointer
					pointer = pointer.next

				pointer.path_weight += node.latency
				pointer.next = node
				pointer = pointer.next
				pointer.path_weight += node.latency
				if node.type is not "io":
					writable = node.get_writable()
					self.register_lookup.update({writable : branch_index})
				else:
					io_index = index
					break		
			if io_index > 0:
				for i in range(1,len(self.instructions)):
					chain = self.instructions[i]
					if i is not io_index:
						ptr = chain
						while (ptr is not None):
							ptr.path_weight += 1
							ptr = ptr.next

	def set_path_weights(self):
		for chain in self.instructions:
			self.path_weights.append(chain.path_weight)

	def adjust_path_weights(self, depends):
		if not bool(depends):
			print("there are no dependencies to check!")
			return
		delta_ptr = None
		for chain_index, chain in enumerate(self.instructions):
			#print("chain_index: "+str(chain))
			ptr = chain
			ptr_path_weight = self.path_weights[chain_index]
			while(ptr is not None):
				ptr_path_weight -= ptr.latency

				if ptr.instruction in depends and ptr.order_number == depends[ptr.instruction][1]:
					if ptr.has_been_fixed:
						self.path_weights[chain_index]+=ptr.fix_latency
					else:
						info_needed = depends[ptr.instruction]
						depend_instruct = info_needed[0]
						ptr_order_number = info_needed[1]
						depend_order_number = info_needed[2]
						fix_const = self.decide_weight(ptr,ptr_path_weight, [depend_instruct, depend_order_number])
						self.path_weights[chain_index] += fix_const

				ptr = ptr.next
	def decide_weight(self, pointer, pointer_weight, target_info):
		for chain_index, chain in enumerate(self.instructions):
			ptr = chain
			ptr_path_weight = self.path_weights[chain_index]
			while(ptr is not None):
				ptr_path_weight -= ptr.latency
				if ptr.instruction in target_info and ptr.order_number in target_info:
					print("dependencies:: "+pointer.instruction+" : "+ptr.instruction)
					dep_potential = pointer_weight+pointer.latency
					ptr_potential = ptr_path_weight+ptr.latency
					if pointer_weight < ptr_path_weight and dep_potential < ptr_potential:
						fix_value = ptr_potential - dep_potential+pointer.latency
						pointer.fix_latency = fix_value#+pointer.latency
						pointer.has_been_fixed = True
						new_potential = pointer_weight+pointer.latency
						print("fix value: "+str(fix_value))
						if new_potential < dep_potential:
							print("we fucked it: check decide_weight")
						return fix_value
					else:
						return 0
				ptr = ptr.next
		print("we fucked it: we weren't supposed to be here (decide_weight)")
		return 0

	def update_chain_times(self, head, target_number, weight):
		ptr = head
		while(ptr is not None):
			ptr.path_weight+=weight
			if ptr.order_number == target_number:
				return
			ptr = ptr.next

	def find_node(self, node_info):
		for chain in self.instructions:
			ptr = chain
			while(ptr is not None):
				if ptr.instruction in node_info and ptr.order_number in node_info:
					return ptr
				ptr = ptr.next
		print("This isn't supposed to happen")
		return None

	def get_path_weight(self, target):
		latency = []
		for chain in self.instructions:
			print("chain: "+chain.instruction)
			count = 0
			pointer = chain
			condition = False
			while(pointer is not None):
				if condition:
					count+=pointer.latency
				if(pointer.instruction == target):
					latency.append(pointer.latency)
					condition = True
				pointer = pointer.next
			if condition:
				latency.append(count)
				return latency
		return [-1,-1]


	def get_read_indecies(self, csv):
		registers = csv.split(",")
		sta = []
		arg1 = self.register_lookup[registers[0]]
		arg2 = self.register_lookup[registers[1]]
		if arg1 == arg2:
			sta.append(arg1[0])
		else:
			for i in arg1:
				sta.append(i)
			for i in arg2:
				if i not in sta:
					sta.append(i)
			# sta.append(arg1[0])
			# sta.append(arg2[0])
		return sta

	def print_instructions(self):
		print("------------------start------------------")
		arr = []
		for b_index, branch in enumerate(self.instructions):
			pointer = branch
			arr.append(pointer.path_weight)
			#print("branch: "+branch.instruction)
			chain = ""
			while True:
				if pointer.next is None:
					chain += pointer.instruction+"---> Null"
					print(str(b_index)+": "+chain)
					break
				else:
					chain += pointer.instruction+"---> "
				pointer = pointer.next
		print(self.path_weights)
		print("------------------end------------------")
