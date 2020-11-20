from nmigen import *
from nmigen.sim.pysim import *

from pixtolic.processor.alu import (
    PixelOperand,
    PixelDestination,
    PixelOpcode,
    PixelALU,
    pixel_instruction_layout,
)
from pixtolic.config.resolutions import resolutions, ResolutionName

def alu_instruction_tb(alu,
                       x_pos, y_pos, frame,
                       expected_result, expected_output):
    yield alu.x_pos.eq(x_pos)
    yield alu.y_pos.eq(y_pos)
    yield alu.frame.eq(frame)
    yield Tick(domain='pixel')
    yield Settle()
    result = yield alu.result
    output = yield alu.output
    assert expected_result == result, f'expected ALU result to be {expected_result:08X}, got {result:08X}'
    assert expected_output == output, f'expected ALU output to be {expected_output:08X}, got {output:08X}'

def alu_tb(alu):
    yield alu.instruction.left_op.eq(PixelOperand.XPOS)
    yield alu.instruction.dest.eq(PixelDestination.OUTPUT)
    yield alu.instruction.opcode.eq(PixelOpcode.NOT)
    yield from alu_instruction_tb(
        alu,
        x_pos=0x2A5,
        y_pos=0,
        frame=0,
        expected_result=0xFFFFFD5A,
        expected_output=0xD5A,
    )

    yield alu.instruction.left_op.eq(PixelOperand.XPOS)
    yield alu.instruction.right_op.eq(PixelOperand.YPOS)
    yield alu.instruction.dest.eq(PixelDestination.OUTPUT)
    yield alu.instruction.opcode.eq(PixelOpcode.SUB)
    yield from alu_instruction_tb(
        alu,
        x_pos=0x123,
        y_pos=0x345,
        frame=0,
        expected_result=0xFFFFFFDE,
        expected_output=0xFDE,
    )

if __name__ == '__main__':
    dut = PixelALU(
        pixel_depth=4,
        resolution=resolutions[ResolutionName.VGA_640_480p_60hz],
        frame_limit=8,
    )
    sim = Simulator(dut)
    def proc():
        yield from alu_tb(dut)
    sim.add_clock(1e-6, domain='pixel')
    sim.add_sync_process(proc, domain='pixel')
    with sim.write_vcd('alu.vcd'):
        sim.run()
