"""Checked C4 references with source-placed wedge feet and measured pad models."""
from build123d import Compound
from rear_foot import assembled_parts


def gen_step():
    parts, _ = assembled_parts()
    return Compound(children=parts, label='C4 with D10 rubber pads - rear rise6mm')
