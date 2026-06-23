"""BrainFlow-backed device: OpenBCI, Muse, Neurosity, synthetic, and more."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register

_BOARD_ALIASES = {
    "synthetic": "SYNTHETIC_BOARD",
    "cyton": "CYTON_BOARD",
    "ganglion": "GANGLION_BOARD",
    "cyton_daisy": "CYTON_DAISY_BOARD",
    "muse_2": "MUSE_2_BOARD",
    "muse_s": "MUSE_S_BOARD",
    "muse_2016": "MUSE_2016_BOARD",
}


class BrainFlowDevice(Device):
    def __init__(self, board: str = "synthetic", serial_port: str = "",
                 mac_address: str = "", uri: str | None = None) -> None:
        from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams

        board_key = _BOARD_ALIASES.get(board, board.upper())
        self._board_id = int(getattr(BoardIds, board_key).value)
        params = BrainFlowInputParams()
        if serial_port:
            params.serial_port = serial_port
        if mac_address:
            params.mac_address = mac_address
        self._shim = BoardShim(self._board_id, params)
        self._eeg_channels = BoardShim.get_eeg_channels(self._board_id)
        sample_rate = float(BoardShim.get_sampling_rate(self._board_id))
        self.info = DeviceInfo(
            name=f"BrainFlow:{board}", uri=uri or f"brainflow://{board}",
            sample_rate=sample_rate, channel_count=len(self._eeg_channels),
            channel_names=[f"ch{i + 1}" for i in range(len(self._eeg_channels))],
            units="uV", extra={"board_id": self._board_id},
        )

    def connect(self) -> None:
        self._shim.prepare_session()

    def start(self) -> None:
        self._shim.start_stream()

    def read(self) -> Chunk | None:
        raw = self._shim.get_board_data()  # (rows, n_samples); empties the ring buffer
        if raw.shape[1] == 0:
            return None
        data = raw[self._eeg_channels, :].astype(np.float32)
        ts = np.arange(data.shape[1], dtype=np.float64) / self.info.sample_rate
        return Chunk(data=data, timestamps=ts)

    def stop(self) -> None:
        if self._shim.is_prepared():
            self._shim.stop_stream()

    def disconnect(self) -> None:
        if self._shim.is_prepared():
            self._shim.release_session()


def _factory(parsed, params):  # noqa: ANN001
    board = parsed.netloc or params.get("board", "synthetic")
    return BrainFlowDevice(
        board=board, serial_port=params.get("serial_port", ""),
        mac_address=params.get("mac_address", ""), uri=parsed.geturl(),
    )


register("brainflow", _factory)
