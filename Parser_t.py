import re
class Parser_t:
	def __init__ (self):
		# self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[2, "arithmatic"], "div":[2, "arithmatic"]}
		# self.memory_latencies = {"load":[3,"load1"], "loadI":[1,"load2"],"loadAI":[3,"load2"], "store":[3,"memory"], "storeAI":[3,"memory"]}
		# self.io_latencies = {"outputAI":[1,"io"]}
		
		self.arithmatic_latencies = {"add":[1, "arithmatic"],"sub":[1, "arithmatic"], "mult":[3, "arithmatic"], "div":[3, "arithmatic"]}
		self.memory_latencies = {"load":[5,"load1"], "loadI":[1,"load2"],"loadAI":[5,"load2"], "store":[5,"memory"], "storeAI":[5,"memory"]}
		self.io_latencies = {"outputAI":[1,"io"]}
		self.register_lookup = {}
		self.potential_dependencies = {}
		self.anti_dependence = {}
		self.last_read_from = {}

	def update_registers(self, writable, value):
		#print(f"registering {value}")
		self.register_lookup.update({writable : value})
	def find_branches(self, instruction_f):
		keyword = instruction_f[0]
		readable = instruction_f[1]
		branch_index = []

		if readable in self.register_lookup:
			branch_index = self.register_lookup[readable]
			#print(f"from parse: {branch_index}")
			return branch_index
		
		csv = readable.split(",")
		# if its not a typo:
			# make it an anti dependence
			# just put the instruction in ig
			# skip over the instruction. don't add it
		arg1 = self.register_lookup[csv[0]]
		arg2 = self.register_lookup[csv[1]]
		if arg1 == arg2:
			branch_index.append(arg1[0])
		else:
			for i in arg1:
				branch_index.append(i)
			for i in arg2:
				if i not in branch_index:
					branch_index.append(i)
		return branch_index



	def parse_instruction(self, instruct, inst_num):
		statement = []	# [instruction, latency, instruction_type]

		# we might actually want to process the instruction
		processed_instruction = self.format_instruction(instruct.split("//")[0].strip())
		statement.append(processed_instruction)

		tokens = processed_instruction.split(" ")
		latencies_array = [self.arithmatic_latencies, self.memory_latencies, self.io_latencies]
		for late_type in latencies_array:
			try:
				late_info = late_type[tokens[0]]
				statement.append(late_info[0]) 	# instruction latency
				statement.append(late_info[1]) 	# instruction type [arithmatic, memory, io]
			except KeyError:
				continue
		# self.find_potential_anti(statement[0], inst_num)
		return statement

	def format_instruction(self, instruction):
		statement = ""
		arithmatic_regex = r"^\s*([a-zA-Z]*)\s*(r\d+)\s*,\s*(r?\d+)\s*=>\s*(r\d+)\s*"
		memory_regex = r"^\s*([a-zA-Z]*)\s*(r?\d+)\s*=>\s*(r\d+)\s*,\s*(r?\d+)\s*"
		load_regex = r"^\s*([a-zA-Z]*)\s*(r?\d+)\s*=>\s*(r\d+)\s*"
		output_regex = r"^\s*([a-zA-Z]*)\s*(r\d+)\s*,\s*(r?\d+)\s*"

		arith = re.search(arithmatic_regex, instruction)
		memory = re.search(memory_regex, instruction)
		load = re.search(load_regex, instruction)
		output = re.search(output_regex, instruction)

		if arith != None:
			#print(1)
			statement = re.sub(arithmatic_regex, r"\1 \2,\3 => \4", instruction)
		elif memory != None:
		    #print(2)
		    statement = re.sub(memory_regex, r"\1 \2 => \3,\4", instruction)
		elif load != None:
		    #print(3)
		    statement = re.sub(load_regex, r"\1 \2 => \3", instruction)
		elif output != None:
		    #print(4)
		    statement = re.sub(output_regex, r"\1 \2,\3", instruction)
		else:
			print("I couldn't find anything bro")

		return statement



	def find_potential_anti(self, instruction, order_number):
		#print(instruction)
		fragment = instruction.split(" ")
		#print(fragment)
		keyword = fragment[0]
		readable = None
		writable = None
		if keyword == "outputAI":
			readable = fragment[1]
			for key,inst_info in self.last_read_from.items():
				if inst_info[1] == order_number-1:
					writable = key
			
		else:
			readable = fragment[1]
			writable = fragment[3]

		imediate = re.search(r"^r?\d*$",readable)
		memory = re.search(r"^r\d*,\d*$",readable)
		if keyword == "outputAI":
			self.last_read_from.update({writable : [instruction, order_number] })
		elif imediate is not None or memory is not None:
			if writable in self.last_read_from:
				prev_info = self.last_read_from[writable]
				#print(f"at instructions {order_number} readable {readable} writable {writable} and k {prev_info}")
				k = prev_info[0]
				ok = prev_info[1]
				#print(f"ok {ok}")
				self.potential_dependencies.update({ k : [instruction, ok, order_number]})
			self.last_read_from.update({readable : [instruction, order_number]})
		else:
			csv = readable.split(",")
			if writable in self.last_read_from:
				info = self.last_read_from[writable]
				k = info[0]
				ok = info[1]
				#print(f"ok {ok}")
				self.potential_dependencies.update({k : [instruction, ok, order_number]})
			self.last_read_from.update({csv[0] : [instruction, order_number]})
			if csv[0] is not csv[1]:
				self.last_read_from.update({csv[1] : [instruction, order_number]})
		#print(self.last_read_from)
		#print()







