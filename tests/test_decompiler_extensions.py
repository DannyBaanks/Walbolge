"""Tests para extensiones de Walbolge: Autobolge conveyor bootstrap, loops y saltos a memoria alta."""
import pytest
from walbolge.decompiler import detect_bootstrap, detect_odometer_loops, decompile
from walbolge.trace import TraceResult, TraceEvent, trace_program


def test_classic_lutter_bootstrap_detected():
    opcodes = "i" + "o" * 99 + "<v"
    b = detect_bootstrap(opcodes)
    assert b is not None
    assert b["kind"] == "bootstrap"
    assert b["opcode_start"] == 0
    assert b["opcode_end"] == 100


def test_autobolge_conveyor_bootstrap_detected():
    # Simulated trace with a quantum jump across sterile gap to c=3315
    trace = TraceResult(
        opcodes="i" + "o" * 10,
        jumps=[{"step": 107, "from_c": 107, "target": 3315}],
        jumps_count=1,
    )
    b = detect_bootstrap("iop", trace=trace)
    assert b is not None
    assert b["kind"] == "bootstrap_conveyor"
    assert b["jump_target"] == 3315
    assert b["sterile_gap"] == [108, 3315]


def test_odometer_cycle5_detected():
    # Sequence of c values repeating with period 5
    events = []
    base_cycle = [10, 11, 12, 13, 14]
    for step in range(50):
        c_val = base_cycle[step % 5]
        events.append(TraceEvent(
            step=step, c=c_val, d=0, a_before=0,
            instruction="p", tape_d=0, event_type="execute"
        ))
    trace = TraceResult(opcodes="p" * 50, events=events)
    loops = detect_odometer_loops(trace)
    assert len(loops) == 1
    assert loops[0]["period"] == 5
    assert loops[0]["type"] == "xlat2_ripple_counter"
    assert loops[0]["confidence"] >= 0.9
