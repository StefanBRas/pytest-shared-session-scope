import dis

def count_yields(func):
    count = 0
    for instr in dis.get_instructions(func):
        if instr.opname == "YIELD_VALUE":
            count += 1
    return count

def has_yield_but_no_cleanup(func) -> bool:
    assert count_yields(func) > 0
    instructions = list(dis.get_instructions(func))
    __import__('pprint').pprint(instructions[-10:])
    return instructions[-6].opname == "YIELD_VALUE"


