"""Minimal example: read brain state without an MCP client."""
import time

from bci_mcp.mcp.service import BrainService


def main() -> None:
    svc = BrainService()
    print(svc.connect("synthetic://?focus=0.8&seed=1"))
    try:
        for _ in range(20):
            time.sleep(0.25)
            state = svc.get_brain_state()
            if "metrics" in state:
                m = state["metrics"]
                print(f"focus={m['focus']:.2f}  calm={m['calm']:.2f}  "
                      f"signal={state['signal_quality']}")
    finally:
        svc.disconnect()


if __name__ == "__main__":
    main()
