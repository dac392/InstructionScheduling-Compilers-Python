import sys
import fileinput
from Scheduler import Scheduler

#constants:
MODE_A = "-a"
MODE_B = "-b"
MODE_C = "-c"

def print_error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
def piping():
	contents = []
	while True:
		try:
			line = input()
		except EOFError:
			break
		contents.append(line)
	return contents

def argument_processing(args):
	mode = -1
	if len(args) < 2 :
		print_error("Use of command:\n  schedule -a/b/c < ILOC file\n")
		sys.exit()
	print_error("------------------------------------------------\n")
	print_error("            Instruction Scheduler\n               415:compilers\n                Spring 2022\n")
	print_error("------------------------------------------------\n")
	if args[1] == "-a":
		print_error("   HEURISTIC: longest latency weighted path\n\n")
		mode = MODE_A
	elif args[1] == "-b":
		print_error("    HEUTISTIC: highest latency instruction\n\n")
		mode = MODE_B
	elif args[1] == "-c":
		print_error("        HEURISTIC: my own\n\n")
		mode = MODE_C
	else:
		print_error(" INVALID HEURISTIC: Use of command:\n  schedule -a/b/c < ILOC file\n")
		sys.exit()
	return mode

def print_instruction(ins):
	for line in ins:
		print(line)
def main(args):
	mode = argument_processing(args)
	instructions = piping()
	ir = Scheduler(mode, instructions)
	ir.schedule()



	print_instruction(instructions)
	print_error("\n-----------------DONE---------------------------\n")

if __name__ == "__main__":
	main(sys.argv)


