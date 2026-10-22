import pickletools, sys, glob, collections
# Static scan: list every global a pickle would import, without executing it.
for f in sys.argv[1:]:
    g = collections.Counter(); stack = []
    with open(f, "rb") as fh:
        for op, arg, pos in pickletools.genops(fh):
            if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE", "BINUNICODE8"):
                stack.append(arg)
            if op.name == "GLOBAL":
                g[arg.replace(" ", ".")] += 1
            elif op.name == "STACK_GLOBAL":
                g[f"{stack[-2]}.{stack[-1]}"] += 1
            if op.name in ("REDUCE", "BUILD", "INST", "OBJ", "NEWOBJ", "NEWOBJ_EX"):
                pass
    print(f.split("external_data/")[-1], dict(g))
