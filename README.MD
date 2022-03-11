# Instruction Scheduling - Compilers - Python
> Instruction Scheduling with 3 Different Heuristics

### Heuristics
1. Longest Latency path (-a): uses the critical path notion to decide which instructions it can schedule next
2. Highest Imediate Latency (-b): only looks at the instructions that are ready and chooses which ever has the highest individual latency
3. Longest Chain (-c): looks at the total chain lengths and tries to excecute the next instruction in the longest chain when ever possible


> To run the script:

'''
	python3 Schedule.py -a < bench.iloc
	python3 Schedule.py -b < bench.iloc
	python3 Schedule.py -b < bench.iloc
'''