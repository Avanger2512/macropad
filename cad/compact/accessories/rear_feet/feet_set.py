"""Two rear and two front feet, all glue faces at Z0, with 4 mm print gaps."""
from build123d import Compound, Pos
from rear_foot import print_foot


def gen_step():
    return Compound(children=[print_foot(), Pos(18, 0, 0) * print_foot(),
                              Pos(0, 18, 0) * print_foot(front=True),
                              Pos(18, 18, 0) * print_foot(front=True)],
                    label='C4 retrofit feet - two rear plus two front D10 pads')
