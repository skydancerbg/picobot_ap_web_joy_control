"""
Desktop test for mecanum mixer (no hardware needed).
Run: python3 tests/test_wheel_map.py
"""


def mix(f, s, r, strafe_sign=1):
    s = s * strafe_sign
    fl = f + s + r
    bl = f - s + r
    fr = f - s - r
    br = f + s - r
    mx = max(abs(fl), abs(bl), abs(fr), abs(br), 100)
    return fl*100/mx, bl*100/mx, fr*100/mx, br*100/mx


def check(label, f, s, r, expect_signs):
    fl, bl, fr, br = mix(f, s, r)
    signs = tuple(
        '+' if v > 0 else ('-' if v < 0 else '0')
        for v in (fl, bl, fr, br)
    )
    ok = signs == tuple(expect_signs)
    status = 'PASS' if ok else 'FAIL'
    print(f"{status}  {label:20s}  fl={fl:+.0f} bl={bl:+.0f} fr={fr:+.0f} br={br:+.0f}  expected={expect_signs}")
    return ok


results = []

# Forward
results.append(check("forward",        100,   0,   0, ['+', '+', '+', '+']))
# Backward
results.append(check("backward",      -100,   0,   0, ['-', '-', '-', '-']))
# Strafe right (X-pattern: FL fwd, BL back, FR back, BR fwd)
results.append(check("strafe right",     0,  50,   0, ['+', '-', '-', '+']))
# Strafe left
results.append(check("strafe left",      0, -50,   0, ['-', '+', '+', '-']))
# Spin CW
results.append(check("spin CW",          0,   0,  50, ['+', '+', '-', '-']))
# Spin CCW
results.append(check("spin CCW",         0,   0, -50, ['-', '-', '+', '+']))
# Diagonal FR
results.append(check("diag fwd-right",  50,  50,   0, ['+', '0', '0', '+']))
# Diagonal BL
results.append(check("diag bck-left",  -50, -50,   0, ['-', '0', '0', '-']))

passed = sum(results)
print(f"\n{passed}/{len(results)} tests passed")
if passed < len(results):
    print("FAIL: check mixer signs and STRAFE_SIGN in config.py")
