import uasyncio as asyncio

# ── shared state ──────────────────────────────────────────────────────────────
_running = False
_task = None

def is_running():
    return _running

def stop():
    global _running
    _running = False

# ── runner ────────────────────────────────────────────────────────────────────

async def start(move_id, speed, set_drive_fn):
    """
    Start a named show-off move. Cancels any currently running move first.
    set_drive_fn(f, s, r) writes to the shared drive target.
    """
    global _task, _running
    if _task is not None:
        _running = False
        try:
            await asyncio.wait_for(_task, timeout=0.3)
        except Exception:
            pass
        _task = None

    moves = {
        'spin':       _spin,
        'moonwalk':   _moonwalk,
        'crab_dash':  _crab_dash,
        'wiggle':     _wiggle,
        'orbit':      _orbit,
        'rear_pivot': _rear_pivot,
        'planet':     _planet,
        'twirl':      _twirl,
        'figure8':    _figure8,
        'tank_drift': _tank_drift,
    }
    fn = moves.get(move_id)
    if fn is None:
        return False
    _running = True
    _task = asyncio.create_task(_guard(fn(speed, set_drive_fn)))
    return True


async def _guard(coro):
    global _running, _task
    try:
        await coro
    finally:
        _running = False
        _task = None


async def _step(ms):
    await asyncio.sleep_ms(ms)


def _ok():
    return _running

# ── individual moves ─────────────────────────────────────────────────────────

async def _spin(speed, drive):
    for _ in range(60):        # ~3 s
        if not _ok(): break
        drive(0, 0, speed)
        await _step(50)
    drive(0, 0, 0)


async def _moonwalk(speed, drive):
    for _ in range(60):
        if not _ok(): break
        drive(-speed // 2, 0, speed)
        await _step(50)
    drive(0, 0, 0)


async def _crab_dash(speed, drive):
    for _ in range(3):
        if not _ok(): break
        drive(0, speed, 0)
        await _step(400)
        if not _ok(): break
        drive(0, -speed, 0)
        await _step(400)
    drive(0, 0, 0)


async def _wiggle(speed, drive):
    for _ in range(6):
        if not _ok(): break
        drive(0, speed, speed // 2)
        await _step(300)
        if not _ok(): break
        drive(0, -speed, -speed // 2)
        await _step(300)
    drive(0, 0, 0)


async def _orbit(speed, drive):
    for _ in range(80):
        if not _ok(): break
        drive(speed // 2, speed // 2, speed // 3)
        await _step(50)
    drive(0, 0, 0)


async def _rear_pivot(speed, drive):
    for _ in range(40):
        if not _ok(): break
        drive(0, 0, speed)
        await _step(50)
    drive(0, 0, 0)


async def _planet(speed, drive):
    import math
    t = 0
    for _ in range(120):
        if not _ok(): break
        f = int(speed * math.sin(t))
        s = int(speed * math.cos(t))
        drive(f, s, speed // 3)
        t += 0.15
        await _step(50)
    drive(0, 0, 0)


async def _twirl(speed, drive):
    fast = min(100, speed * 2)
    for _ in range(20):
        if not _ok(): break
        drive(0, 0, fast)
        await _step(50)
    drive(0, 0, 0)


async def _figure8(speed, drive):
    half = speed // 2
    for _ in range(2):
        for r in (half, -half):
            for _ in range(40):
                if not _ok(): break
                drive(speed, 0, r)
                await _step(50)
    drive(0, 0, 0)


async def _tank_drift(speed, drive):
    for _ in range(30):
        if not _ok(): break
        drive(speed, 0, speed // 2)
        await _step(50)
    for _ in range(20):
        if not _ok(): break
        drive(0, 0, -speed)
        await _step(50)
    drive(0, 0, 0)
