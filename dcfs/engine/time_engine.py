class TimeEngine:
    """Controls wall-clock delay by simulation mode."""

    MODE_STEP_SECONDS = {
        "real_time": 1.0,
        "fast": 0.1,
        "chaos": 0.5,
    }

    def __init__(self, mode="real_time", step_seconds=None):
        if mode not in self.MODE_STEP_SECONDS:
            raise ValueError(f"Unsupported simulation mode: {mode}")
        self.mode = mode
        self.step_seconds = (
            float(step_seconds)
            if step_seconds is not None
            else self.MODE_STEP_SECONDS[mode]
        )

