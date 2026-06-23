"""Record a synthetic session, then load it and print band powers."""
import numpy as np

from bci_mcp.dsp import bands, filters
from bci_mcp.pipeline import Pipeline
from bci_mcp.recording.reader import load_recording


def main() -> None:
    pipe = Pipeline("synthetic://?focus=0.7&seed=1")
    pipe.start()
    try:
        import time

        time.sleep(0.5)
        path = pipe.record(seconds=2.0, path="demo_session.npz")
        print("saved", path)
    finally:
        pipe.stop()

    rec = load_recording(path)
    filtered = filters.bandpass(rec.data, rec.sample_rate)
    print("band powers:", bands.band_powers(filtered, rec.sample_rate))


if __name__ == "__main__":
    main()
