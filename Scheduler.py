from InstructionList import InstructionList
import re
class Scheduler:
	def __init__(self, mode, instructions):
		self.mode = mode
		self.instructions = instructions
		self.scheduled = []
		self.last_read_from = {}	# key: [insruction, key_number] 
		self.i = {}
		self.ignorable = {}
		self.anti_dependencies = {} # key: [instruction, key_number, instruction_number]

	def schedule(self):
		execute = {"-a":self.longest_latency, "-b":self.highest_latency, "-c":self.my_own};
		execute[self.mode]()

	def longest_latency(self):
		IL = InstructionList()
		order = 1
		for line in self.instructions:
			line_info = self.parse_instruction(line, IL)
			self.find_all_potential_anti(line_info[0], order)
			IL.add_instruction(line_info, order)
			order+=1
		self.find_dependence(IL)
		print(self.anti_dependencies)
		IL.set_path_weights()
		IL.adjust_path_weights(self.anti_dependencies)
		
		#actual scheduling:

		
		IL.print_instructions()
	
	def dependencies_are_equal(self,node):
		info = self.anti_dependencies[node.instruction]
		if info[1] == node.order_number:
			return True
		return False

	def find_dependence(self, il):
		fuck_yea = {}
		for chain in il.instructions:
			anti_key_orders = {}
			ptr = chain
			while(ptr is not None):
				instruct = ptr.instruction
				if instruct in self.anti_dependencies and self.dependencies_are_equal(ptr):
					info = self.anti_dependencies[instruct]
					#print("add: "+instruct+" :: "+str(info))
					v = info[0]
					ok1 = info[1]
					ok2 = info[2]
					anti_key_orders.update({v : [instruct, ok1, ok2]})

				elif instruct in anti_key_orders:
					anti_info = anti_key_orders[instruct]
					k = anti_info[0]
					ok1 = anti_info[1]
					ok2 = anti_info[2]
					info_2 = self.anti_dependencies[k]
					if instruct == info_2[0] and ok1 == info_2[1] and ok2 == info_2[2]:
						anti_key_orders.pop(instruct)
						#print("pop: "+instruct+" :: "+str(anti_info))

				ptr = ptr.next
			#print("remaining in chain: "+str(anti_key_orders))
			if bool(anti_key_orders):
				for anti_k,anti_v in anti_key_orders.items():
					k = anti_v[0]
					ok1 = anti_v[1]
					ok2 = anti_v[2]
					fuck_yea.update({k : [anti_k, ok1, ok2]})
		self.anti_dependencies.clear()
		for k,v in fuck_yea.items():
			self.anti_dependencies.update({k : v})

	def find_all_potential_anti(self, instruction, order_number):
		#print(instruction)
		fragment = instruction.split(" ")
		#print(fragment)
		keyword = fragment[0]
		if keyword == "outputAI":
			return
		readable = fragment[1]
		writable = fragment[3]
		imediate = re.search(r"^r?\d*$",readable)
		memory = re.search(r"^r\d*,\d*$",readable)
		if imediate is not None or memory is not None:
			if writable in self.last_read_from:
				prev_info = self.last_read_from[writable]
				k = prev_info[0]
				ok = prev_info[1]
				self.anti_dependencies.update({ k : [instruction, ok, order_number]})
			self.last_read_from.update({readable : [instruction, order_number]})
		else:
			csv = readable.split(",")
			if writable in self.last_read_from:
				info = self.last_read_from[writable]
				k = info[0]
				ok = info[1]
				self.anti_dependencies.update({k : [instruction, ok, order_number]})
			self.last_read_from.update({csv[0] : [instruction, order_number]})
			if csv[0] is not csv[1]:
				self.last_read_from.update({csv[1] : [instruction, order_number]})

	def parse_instruction(self, instruct, IList):
		statement = []	# [instruction, latency, instruction_type]

		# we might actually want to process the instruction
		processed_instruction = self.format_instruction(instruct.split("//")[0].strip())
		statement.append(processed_instruction)

		tokens = processed_instruction.split(" ")
		latencies_array = [IList.arithmatic_latencies, IList.memory_latencies, IList.io_latencies]
		for late_type in latencies_array:
			try:
				late_info = late_type[tokens[0]]
				statement.append(late_info[0]) 	# instruction latency
				statement.append(late_info[1]) 	# instruction type [arithmatic, memory, io]
			except KeyError:
				continue
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
	

	def highest_latency(self):
		print("mode b")
	def my_own(self):
		print("mode c")

