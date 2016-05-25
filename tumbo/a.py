from pip.req import parse_requirements
install_reqs = parse_requirements("./requirements.txt")
install_reqs1 = parse_requirements("./requirements.txt")
reqs = [str(ir.req) for ir in install_reqs if not "github" in str(ir.url)]
deps = [str(ir.url) for ir in install_reqs1 if "github" in str(ir.url)]
print reqs
print "****"
print deps
