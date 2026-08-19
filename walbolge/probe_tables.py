import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from walbolge.tables import ENCRYPTION_TRANSLATE, _CRAZY_TABLE, TERNARY_DIGITS

PIP_ENCRYPT = (
    "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB"
    "6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
)
PIP_CRAZY = (
    (1, 0, 0),
    (1, 0, 2),
    (2, 2, 1),
)

print("len walbolge:", len(ENCRYPTION_TRANSLATE), "| len pip:", len(PIP_ENCRYPT))
print("ENCRYPTION_TRANSLATE == pip ENCRYPT:", ENCRYPTION_TRANSLATE == PIP_ENCRYPT)
if ENCRYPTION_TRANSLATE != PIP_ENCRYPT:
    first = next(i for i, (a, b) in enumerate(zip(ENCRYPTION_TRANSLATE, PIP_ENCRYPT)) if a != b)
    print("primer diff en índice", first, ":", repr(ENCRYPTION_TRANSLATE[first]), "vs", repr(PIP_ENCRYPT[first]))
    print("walbolge segmento:", ENCRYPTION_TRANSLATE[max(0, first-10):first+10])
    print("pip segmento     :", PIP_ENCRYPT[max(0, first-10):first+10])

print("CRAZY_TABLE walbolge:", CRAZY_TABLE)
print("CRAZY_TABLE pip     :", PIP_CRAZY)
print("crazy igual:", CRAZY_TABLE == PIP_CRAZY)
print("TERNARY_DIGITS:", TERNARY_DIGITS)
