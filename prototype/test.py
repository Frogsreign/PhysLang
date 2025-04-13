from syzygy.parse import parse


if __name__ == '__main__':
    sss = open("./tests/data/solar_system.json", "r").read()

    script = """point(pos=[x, y, z], vel=[x, y, z], acc=[x, y ,z], m=1, e=1)
update(input=[A, B], output=A.vel, func=\"3 * A.mass + B.mass * (norm(A.vel) + B.mass)\")
force(input=[A,B], func=\"3 * particle_1_first.mass * B.mass * (A.pos[0] - B.pos_123_p[0]) / norm(A.pos - B.pos)^2 \")"""


    ast = parse.build_entire_ast(script)
    print(ast)
