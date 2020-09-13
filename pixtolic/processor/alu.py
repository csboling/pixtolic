from enum import Enum
from math import log2

from nmigen import * 


class PixelOperand(Enum):
    GP0    = 0
    GP1    = 1
    GP2    = 2
    GP3    = 3
    XPOS   = 4
    YPOS   = 5
    FRAME  = 6
    IMM    = 7

class PixelDestination(Enum):
    GP0    = 0
    GP1    = 1
    GP2    = 2
    GP3    = 3
    OUTPUT = 7
    
class PixelOpcode(Enum):
    NOT = 0
    AND = 1
    OR  = 2
    XOR = 3
    ADD = 4
    SUB = 5

REGISTER_COUNT = 4
REGISTER_WIDTH = 32

pixel_instruction_layout = [
    ('left_op', len(PixelOperand.__members__).bit_length()),
    ('right_op', len(PixelOperand.__members__).bit_length()),
    ('dest', len(PixelDestination.__members__).bit_length()),
    ('opcode', len(PixelOpcode.__members__).bit_length()),
    ('immediate', REGISTER_WIDTH),
]


class PixelALU(Elaboratable):
    def __init__(self, pixel_depth, resolution, frame_limit):
        self.pixel_depth = pixel_depth

        self.instruction = Record(pixel_instruction_layout)
        self.x_pos = Signal((resolution.width).bit_length())
        self.y_pos = Signal((resolution.height).bit_length())
        self.frame = Signal((frame_limit).bit_length())

        self.left = Signal(REGISTER_WIDTH)
        self.right = Signal(REGISTER_WIDTH)
        self.result = Signal(REGISTER_WIDTH)
        self.output = Signal(3 * self.pixel_depth)
        self.registers = Array(
            Signal(REGISTER_WIDTH) for _ in range(REGISTER_COUNT)
        )

    def elaborate(self, platform):
        m = Module()

        self.pick_operand(m, 'left_op', 'left')
        self.pick_operand(m, 'right_op', 'right')

        with m.Switch(self.instruction.opcode):
            with m.Case(PixelOpcode.NOT):
                m.d.comb += self.result.eq(~self.left)
            with m.Case(PixelOpcode.AND):
                m.d.comb += self.result.eq(self.left & self.right)
            with m.Case(PixelOpcode.OR):
                m.d.comb += self.result.eq(self.left | self.right)
            with m.Case(PixelOpcode.XOR):
                m.d.comb += self.result.eq(self.left ^ self.right)
            with m.Case(PixelOpcode.ADD):
                m.d.comb += self.result.eq(self.left + self.right)
            with m.Case(PixelOpcode.SUB):
                m.d.comb += self.result.eq(self.left - self.right)

        with m.If(self.instruction.dest == PixelDestination.OUTPUT):
            m.d.pixel += self.output.eq(self.result)
        with m.Else():
            self.registers[self.instruction.dest].eq(self.result)

        return m

    def pick_operand(self, m, sel_attr, data_attr):
        sel = getattr(self.instruction, sel_attr)
        data = getattr(self, data_attr)
        with m.Switch(sel):
            with m.Case(PixelOperand.XPOS):
                m.d.comb += data.eq(self.x_pos)
            with m.Case(PixelOperand.YPOS):
                m.d.comb += data.eq(self.y_pos)
            with m.Case(PixelOperand.FRAME):
                m.d.comb += data.eq(self.frame)
            with m.Case(PixelOperand.IMM):
                m.d.comb += data.eq(self.instruction.immediate)
            with m.Default():
                m.d.comb += data.eq(self.registers[sel & 0x3])

    def slice_pixels(self, reg):
        yield reg[0:4]
        yield reg[4:8]
        yield reg[8:12]
