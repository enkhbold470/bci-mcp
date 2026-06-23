"""NeuroFocus v4 device — USB-serial and BLE transports."""
from __future__ import annotations

import threading
import time

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register
from . import neurofocus_protocol as proto


class NeuroFocusDevice(Device):
    def __init__(self, transport: str = "serial", port: str = "",
                 ble_name: str = "NEUROFOCUS_V4_01",
                 sample_rate: float = proto.DEFAULT_SAMPLE_RATE,
                 baud: int = 115200, uri: str | None = None,
                 serial_factory=None) -> None:
        self.transport = transport
        self.port = port
        self.ble_name = ble_name
        self.baud = baud
        self._serial_factory = serial_factory
        self.info = DeviceInfo(
            name=f"NeuroFocus v4 ({transport})",
            uri=uri or (f"neurofocus://serial/{port}" if transport == "serial"
                        else f"neurofocus://ble/{ble_name}"),
            sample_rate=sample_rate, channel_count=1, channel_names=["ch1"],
            units="uV", extra={"transport": transport},
        )
        self._buf: list[float] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self._serial = None
        self._ble_client = None
        self._loop = None

    # --- shared ---
    def _emit_counts(self, counts) -> None:
        if not counts:
            return
        uv = proto.counts_to_uv(np.asarray(counts, dtype=np.int64))
        with self._lock:
            self._buf.extend(float(x) for x in np.atleast_1d(uv))

    def read(self) -> Chunk | None:
        with self._lock:
            if not self._buf:
                return None
            values = self._buf
            self._buf = []
        data = np.array(values, dtype=np.float32).reshape(1, -1)
        ts = np.arange(data.shape[1], dtype=np.float64) / self.info.sample_rate
        return Chunk(data=data, timestamps=ts)

    # --- lifecycle dispatch ---
    def connect(self) -> None:
        if self.transport == "serial":
            self._connect_serial()
        else:
            self._connect_ble()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self.transport == "serial":
            self._serial.write(proto.CMD_START)
            self._thread = threading.Thread(target=self._run_serial, daemon=True)
            self._thread.start()
        # BLE auto-streams on connect; notifications already flowing.

    def stop(self) -> None:
        self._running = False
        if self.transport == "serial" and self._serial is not None:
            try:
                self._serial.write(proto.CMD_STOP)
            except (OSError, AttributeError):
                pass
            if self._thread is not None:
                self._thread.join(timeout=1.0)

    def disconnect(self) -> None:
        if self.transport == "serial":
            if self._serial is not None and getattr(self._serial, "is_open", False):
                self._serial.close()
        else:
            self._disconnect_ble()

    # --- serial transport ---
    def _connect_serial(self) -> None:
        if self._serial_factory is not None:
            self._serial = self._serial_factory(self.port, self.baud)
        else:
            import serial

            self._serial = serial.Serial(self.port, self.baud, timeout=1)

    def _run_serial(self) -> None:
        while self._running and getattr(self._serial, "is_open", False):
            try:
                if self._serial.in_waiting:
                    line = self._serial.readline()
                    self._emit_counts(proto.parse_frame(line))
                else:
                    time.sleep(0.001)
            except (OSError, AttributeError):
                break

    # --- BLE transport (bleak 3.x API verified: find_device_by_name, start_notify(uuid, cb),
    #     callback signature (sender, data: bytearray)) ---
    def _connect_ble(self) -> None:
        import asyncio

        import bleak

        self._loop = asyncio.new_event_loop()

        def _notify(_sender, data: bytearray) -> None:
            self._emit_counts(proto.parse_frame(bytes(data)))

        async def _setup() -> None:
            device = await bleak.BleakScanner.find_device_by_name(self.ble_name)
            if device is None:
                raise RuntimeError(f"NeuroFocus BLE device '{self.ble_name}' not found")
            self._ble_client = bleak.BleakClient(device)
            await self._ble_client.connect()
            await self._ble_client.start_notify(proto.DATA_CHAR_UUID, _notify)
            await self._ble_client.write_gatt_char(proto.CMD_CHAR_UUID, proto.CMD_START)

        def _run_loop() -> None:
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(_setup())
            self._loop.run_forever()

        self._running = True
        self._thread = threading.Thread(target=_run_loop, daemon=True)
        self._thread.start()
        time.sleep(0.1)  # give the loop a moment to start connecting

    def _disconnect_ble(self) -> None:
        self._running = False
        if self._loop is not None and self._ble_client is not None:
            import asyncio

            async def _teardown() -> None:
                try:
                    await self._ble_client.stop_notify(proto.DATA_CHAR_UUID)
                except Exception:  # noqa: BLE001
                    pass
                await self._ble_client.disconnect()

            try:
                fut = asyncio.run_coroutine_threadsafe(_teardown(), self._loop)
                fut.result(timeout=2.0)
            except Exception:  # noqa: BLE001
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)


def _factory(parsed, params):  # noqa: ANN001
    # neurofocus://serial/<port>  or  neurofocus://ble/<name>
    transport = parsed.netloc or "serial"
    rest = parsed.path.lstrip("/")
    if transport == "serial":
        port = "/" + rest if rest else ""
        return NeuroFocusDevice(transport="serial", port=port,
                                uri=parsed.geturl())
    return NeuroFocusDevice(transport="ble", ble_name=rest or "NEUROFOCUS_V4_01",
                            uri=parsed.geturl())


register("neurofocus", _factory)
