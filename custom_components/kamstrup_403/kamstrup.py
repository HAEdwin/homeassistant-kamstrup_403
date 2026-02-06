"""Kamstrup Meter Protocol (KMP) client."""

import asyncio
import logging
import math

import serial_asyncio_fast as serial_asyncio

from .const import ESCAPES, UNITS

_LOGGER = logging.getLogger(__name__)


class Kamstrup:
    """Kamstrup Meter Protocol (KMP) client."""

    def __init__(self, port: str, baudrate: int = 1200, timeout: float = 1.0) -> None:
        """Initialize."""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        """Connect to the serial device."""
        if self._reader is None or self._writer is None:
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self.port, baudrate=self.baudrate
            )

    async def disconnect(self) -> None:
        """Disconnect from the serial device."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None

    @staticmethod
    def _crc(message: bytes) -> int:
        """Calculate CCITT CRC-16."""
        poly, reg = 0x1021, 0x0000
        for byte in message:
            mask = 0x80
            while mask > 0:
                reg <<= 1
                if byte & mask:
                    reg |= 1
                mask >>= 1
                if reg & 0x10000:
                    reg &= 0xFFFF
                    reg ^= poly
        return reg

    async def _write(self, data: bytes) -> None:
        """Write to meter."""
        if self._writer is None:
            await self.connect()
        self._writer.write(data)
        await self._writer.drain()

    async def _read_byte(self) -> int | None:
        """Read single byte with timeout."""
        if self._reader is None:
            await self.connect()
        try:
            data = await asyncio.wait_for(self._reader.read(1), timeout=self.timeout)
            return data[0] if data else None
        except asyncio.TimeoutError:
            return None

    async def _send(self, message: tuple[int, ...]) -> None:
        """Send message with CRC and escaping."""
        msg = bytearray(message) + b"\x00\x00"
        crc = self._crc(bytes(msg))
        msg[-2], msg[-1] = crc >> 8, crc & 0xFF

        data = bytearray([0x80])
        for b in msg:
            if b in ESCAPES:
                data.extend([0x1B, b ^ 0xFF])
            else:
                data.append(b)
        data.append(0x0D)
        await self._write(bytes(data))

    async def _receive(self) -> bytearray | None:
        """Receive and decode response."""
        buf = None
        while True:
            b = await self._read_byte()
            if b is None:
                return None
            if b == 0x40:
                buf = bytearray()
            if buf is not None:
                buf.append(b)
                if b == 0x0D:
                    break

        # Remove escaping
        result, i = bytearray(), 1
        while i < len(buf) - 1:
            if buf[i] == 0x1B:
                result.append(buf[i + 1] ^ 0xFF)
                i += 2
            else:
                result.append(buf[i])
                i += 1

        if self._crc(bytes(result)):
            _LOGGER.debug("CRC error")
            return None
        return result[:-2]

    @staticmethod
    def _decode_value(data: bytearray) -> tuple[float | None, str | None]:
        """Decode a value from response data."""
        unit = UNITS.get(data[2])
        value = 0.0
        for i in range(data[3]):
            value = value * 256 + data[i + 5]

        exp_val = data[4] & 0x3F
        if data[4] & 0x40:
            exp_val = -exp_val
        exp = math.pow(10, exp_val)
        if data[4] & 0x80:
            exp = -exp
        return value * exp, unit

    async def read_registers(
        self, registers: list[int]
    ) -> dict[int, tuple[float | None, str | None]]:
        """Read multiple registers (max 8 at a time)."""
        registers = registers[:8]
        req = [0x3F, 0x10, len(registers)]
        for r in registers:
            req.extend([r >> 8, r & 0xFF])
        await self._send(tuple(req))

        data = await self._receive()
        if data is None or len(data) < 3 or data[0] != 0x3F or data[1] != 0x10:
            return {}

        result = {}
        remaining = data[2:]
        for reg in registers:
            if len(remaining) < 6:
                break
            if remaining[0] == reg >> 8 and remaining[1] == reg & 0xFF:
                value, unit = self._decode_value(remaining)
                result[reg] = (value, unit)
                remaining = remaining[5 + remaining[3] :]
            else:
                result[reg] = (None, None)
        return result
