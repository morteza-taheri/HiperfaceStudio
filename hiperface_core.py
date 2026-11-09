# -*- coding: utf-8 -*-
"""
HIPERFACE Studio - core (protocol, simulator, helpers, worker)
GUI terminal for SICK HIPERFACE(R) encoders over RS-485.
Protocol per SICK "Operating Instructions - Specification HIPERFACE Motor
Feedback Protocol" (8010701 / IM0064865), command codes from Table 10.

Pure Python + tkinter + pyserial. Compatible with Python 3.8 (Windows 7 SP1+).
"""
import sys
import os
import time
import json
import struct
import queue
import threading
import datetime
import math

try:
    import serial
    import serial.tools.list_ports
except ImportError:  # pragma: no cover
    serial = None

APP_NAME = "HIPERFACE Studio"
APP_VERSION = "1.2.0"
DEMO_PORT = "DEMO (simulated)"


# =============================================================================
#  Protocol layer  (checked against IM0064865, 8010701/1EEB/2021-12-15)
# =============================================================================
class HiperfaceError(Exception):
    def __init__(self, msg, code=None, warning=False):
        Exception.__init__(self, msg)
        self.code = code
        self.warning = warning


# Table 10: max. response time of the Slave in ms (after the Master request timeout)
RESPONSE_TIME_MS = {0x42: 10, 0x43: 40, 0x44: 5, 0x46: 5, 0x47: 30, 0x49: 30, 0x4A: 30, 0x4B: 250, 0x4C: 5,
                    0x4D: 70, 0x4E: 5, 0x4F: 40, 0x50: 5, 0x52: 5, 0x55: 40, 0x56: 5, 0x57: 40, 0x67: 5,
                    0x6A: 40, 0x6B: 40, 0x6C: 30}

BAUD_MAP = {0: 600, 1: 1200, 2: 2400, 3: 4800, 4: 9600, 5: 19200, 6: 38400}
PARITY_MAP = {0: "N", 2: "E", 3: "O"}          # bits 4..5 of the UART settings byte
DEFAULT_UART = 0xE4                             # 9600 Bd, even parity, 5x timeout, standard slave


def uart_to_port(b):
    """UART settings byte -> (baud, parity letter) or raises ValueError."""
    baud = BAUD_MAP.get(b & 0x07)
    parity = PARITY_MAP.get((b >> 4) & 0x03)
    if baud is None or parity is None:
        raise ValueError("UART settings byte 0x%02X is not valid" % b)
    return baud, parity


def apply_uart_to_port(ser, b):
    baud, parity = uart_to_port(b)
    ser.baudrate = baud
    ser.parity = parity
    return baud, parity


class HiperfaceEncoder(object):
    DEFAULT_ADDR = 0x40
    BROADCAST = 0xFF
    DEFAULT_CODE0 = 0x55
    EXT_TYPE_FIELD = 0xFF

    CMD_READ_POS = 0x42
    CMD_SET_POS = 0x43
    CMD_READ_ANALOG = 0x44
    CMD_READ_COUNTER = 0x46
    CMD_INC_COUNTER = 0x47
    CMD_CLEAR_COUNTER = 0x49
    CMD_READ_DATA = 0x4A
    CMD_SAVE_DATA = 0x4B
    CMD_DATA_STATUS = 0x4C
    CMD_CREATE_FIELD = 0x4D
    CMD_READ_MEM = 0x4E
    CMD_CHANGE_ACCESS = 0x4F
    CMD_READ_STATUS = 0x50
    CMD_READ_TYPE = 0x52
    CMD_RESET = 0x53
    CMD_ALLOC_ADDR = 0x55
    CMD_READ_SERIAL_VER = 0x56
    CMD_CONFIG_SERIAL = 0x57
    CMD_TEMP_SET_SERIAL = 0x67
    CMD_SET_POS_SYNC = 0x6A
    CMD_SENSOR_ADJUST = 0x6B
    CMD_READ_SYNC_OFFSET = 0x6C

    FAULT_CODES = {
        0x00: "No error",
        0x01: "Analog signals outside specification",
        0x02: "Wrong internal angular offset",
        0x03: "Data field partitioning table destroyed",
        0x04: "Analog limit values not available",
        0x05: "Internal I2C bus inoperable",
        0x06: "Internal checksum error",
        0x07: "Encoder reset by program watchdog",
        0x08: "Counter overflow",
        0x09: "Parity error",
        0x0A: "Checksum of transmitted data wrong",
        0x0B: "Unknown command code",
        0x0C: "Wrong number of transmitted data",
        0x0D: "Command argument not allowed",
        0x0E: "Data field is read-only",
        0x0F: "Wrong access code",
        0x10: "Memory full / field size cannot be changed",
        0x11: "Data field offset out of range",
        0x12: "Data field does not exist",
        0x1C: "Analog signal monitoring warning",
        0x1D: "Transmitter (LED) current critical",
        0x1E: "Encoder temperature critical",
        0x1F: "Speed too high",
        0x20: "Singleturn position unreliable / not calibrated",
        0x21: "Multiturn amplitude error",
        0x22: "Multiturn synchronisation error",
        0x23: "Multiturn vector length error",
        0x24: "Multiturn counter error",
    }

    BAUD_MAP = BAUD_MAP

    def __init__(self, ser, address=DEFAULT_ADDR, code0=DEFAULT_CODE0, on_frame=None, on_warning=None,
                 margin_ms=100):
        self.ser = ser
        self.addr = address
        self.code0 = code0
        self.on_frame = on_frame
        self.on_warning = on_warning
        self.margin = max(0, margin_ms) / 1000.0
        self.warning = False          # last response had the warning bit (bit 7) set
        self.pending_uart = None      # written with 57h, becomes active after 53h / power cycle
        self._last_io = 0.0
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except Exception:
            pass

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def crc(data):
        """XOR over all frame bytes including address (spec 2.3.3)."""
        c = 0
        for b in bytearray(data):
            c ^= b
        return c

    def _emit(self, direction, data):
        if self.on_frame:
            try:
                self.on_frame(direction, bytes(data))
            except Exception:
                pass

    def _baud(self):
        try:
            return int(getattr(self.ser, "baudrate", 9600) or 9600)
        except Exception:
            return 9600

    def char_time(self):
        """Seconds per UART character: start + 8 data + parity + stop."""
        bits = 10 if getattr(self.ser, "parity", "E") == "N" else 11
        return bits / float(self._baud())

    def timeout_condition(self):
        """Longest programmable frame timeout: 55 s / data rate (spec 2.2.2, 5.73 ms at 9600)."""
        return 55.0 / self._baud()

    def _pause(self):
        """The end of every frame must be followed by a pause of at least the timeout condition."""
        wait = self._last_io + self.timeout_condition() * 1.2 - time.time()
        if wait > 0:
            time.sleep(wait)

    def _available(self):
        n = getattr(self.ser, "in_waiting", None)
        if n is None:
            return -1
        return n

    def _read_frame(self, total, sent_cmd, timeout_s):
        """Read one Slave frame. Ends at the expected length, after an inter-byte gap or at the deadline."""
        buf = bytearray()
        deadline = time.time() + timeout_s
        gap = max(0.035, self.timeout_condition() * 3)       # USB adapters deliver in ~16 ms chunks
        last = None
        while True:
            n = self._available()
            if n == -1:                                        # port object without in_waiting
                chunk = self.ser.read(1)
                n = len(chunk)
                if chunk:
                    buf += chunk
            elif n > 0:
                want = n if total is None else min(n, max(1, total - len(buf)))
                buf += self.ser.read(want)
            now = time.time()
            if n:
                last = now
                if len(buf) >= 2 and (buf[1] & 0x7F) == self.CMD_READ_STATUS and sent_cmd != self.CMD_READ_STATUS:
                    total = 4                                  # error frame: addr, 50h/D0h, code, checksum
                if total is not None and len(buf) >= total:
                    break
                continue
            if last is not None and now - last > gap:
                break
            if now > deadline:
                break
            time.sleep(0.001)
        return bytes(buf)

    def _send_cmd(self, cmd, data_bytes=b"", slave_len=None, wait_response=True, resp_addr=None):
        """Send [addr][cmd][data][xor] and return the validated response frame.

        slave_len: number of Slave data bytes per the spec (None = variable / not specified)."""
        packet = bytearray([self.addr, cmd]) + bytearray(data_bytes)
        packet.append(self.crc(packet))
        self._pause()
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass
        self.ser.write(bytes(packet))
        try:
            self.ser.flush()
        except Exception:
            pass
        self._emit("TX", packet)
        if not wait_response:
            self._last_io = time.time()
            return b""

        total = None if slave_len is None else slave_len + 3
        ct = self.char_time()
        tmo = (RESPONSE_TIME_MS.get(cmd, 250) / 1000.0 + (len(packet) + (total or 40)) * ct
               + self.timeout_condition() * 2 + self.margin)
        resp = self._read_frame(total, cmd, tmo)
        self._last_io = time.time()
        if not resp:
            raise HiperfaceError("No response from encoder (timeout)")
        self._emit("RX", resp)
        if len(resp) < 3:
            raise HiperfaceError("Incomplete response: %s" % hex_spaced(resp))
        expected = self.crc(resp[:-1])
        if expected != resp[-1]:
            raise HiperfaceError("Checksum mismatch: expected 0x%02X, got 0x%02X" % (expected, resp[-1]))
        want_addr = self.addr if resp_addr is None else resp_addr
        if want_addr == self.BROADCAST:
            if not (0x40 <= resp[0] <= 0x5F):
                raise HiperfaceError("Response from invalid address 0x%02X" % resp[0])
        elif resp[0] != want_addr:
            raise HiperfaceError("Response from address 0x%02X, expected 0x%02X" % (resp[0], want_addr))

        c = resp[1]
        warn = bool(c & 0x80)
        self.warning = warn
        if warn and self.on_warning:
            try:
                self.on_warning(cmd)
            except Exception:
                pass
        if (c & 0x7F) == self.CMD_READ_STATUS and cmd != self.CMD_READ_STATUS:
            code = resp[2] if len(resp) >= 4 else None
            if code is None:
                raise HiperfaceError("Malformed error response: %s" % hex_spaced(resp), warning=warn)
            raise HiperfaceError("Encoder error 0x%02X: %s%s" % (
                code, self.FAULT_CODES.get(code, "Unknown fault code"),
                " (+ pending warning, read status 50h)" if warn else ""), code=code, warning=warn)
        if (c & 0x7F) != cmd:
            raise HiperfaceError("Unexpected command byte 0x%02X in response (sent 0x%02X)" % (c, cmd))
        if total is not None and len(resp) != total:
            raise HiperfaceError("Wrong response length: %d bytes, expected %d" % (len(resp), total))
        return resp

    @staticmethod
    def _data(resp):
        return bytes(resp[2:-1])

    # --------------------------------------------------------------- commands
    def read_position(self):
        """42h: absolute position, unsigned 32 bit, MSB first (5 bits per sin/cos period)."""
        r = self._send_cmd(self.CMD_READ_POS, slave_len=4)
        return struct.unpack(">I", r[2:6])[0]

    def set_position(self, value):
        """43h: position preset + Code0. Motor must be at standstill."""
        d = struct.pack(">I", value & 0xFFFFFFFF) + bytes([self.code0 & 0xFF])
        self._send_cmd(self.CMD_SET_POS, d, slave_len=0)
        return True

    def read_analog(self, channel):
        """44h: Slave data = CHANNEL echo + 16-bit value."""
        r = self._send_cmd(self.CMD_READ_ANALOG, bytes([channel & 0xFF]), slave_len=3)
        if r[2] != (channel & 0xFF):
            raise HiperfaceError("Channel echo 0x%02X does not match request 0x%02X" % (r[2], channel))
        return struct.unpack(">H", r[3:5])[0]

    def read_temperature(self):
        """Channel 48h: 1 degC steps, signed 16 bit (2's complement)."""
        raw = self.read_analog(0x48)
        return struct.unpack(">h", struct.pack(">H", raw))[0], raw

    def read_counter(self):
        """46h: 24-bit non-volatile counter."""
        r = self._send_cmd(self.CMD_READ_COUNTER, slave_len=3)
        return struct.unpack(">I", b"\x00" + r[2:5])[0]

    def increment_counter(self):
        self._send_cmd(self.CMD_INC_COUNTER, slave_len=0)
        return True

    def clear_counter(self):
        """49h: reset counter, needs Code0."""
        self._send_cmd(self.CMD_CLEAR_COUNTER, bytes([self.code0 & 0xFF]), slave_len=0)
        return True

    def read_data(self, field_id, offset=0, num_bytes=16, access_code=None):
        """4Ah: [field][offset][count][access code] -> [field][offset][count][data...]"""
        if not (1 <= num_bytes <= 128):
            raise HiperfaceError("Number of bytes must be 1..128")
        ac = self.code0 if access_code is None else access_code
        d = bytes([field_id & 0xFF, offset & 0xFF, num_bytes & 0xFF, ac & 0xFF])
        r = self._send_cmd(self.CMD_READ_DATA, d, slave_len=3 + num_bytes)
        if r[2] != (field_id & 0xFF) or r[3] != (offset & 0xFF) or r[4] != num_bytes:
            raise HiperfaceError("Echoed field/offset/length do not match request")
        return bytes(r[5:5 + num_bytes])

    def save_data(self, field_id, offset, data, access_code=None):
        """4Bh: [field][offset][count][access code][data...] -> [field][offset][count]"""
        data = bytes(data)
        if not (1 <= len(data) <= 128):
            raise HiperfaceError("Data must be 1..128 bytes")
        ac = self.code0 if access_code is None else access_code
        d = bytes([field_id & 0xFF, offset & 0xFF, len(data), ac & 0xFF]) + data
        r = self._send_cmd(self.CMD_SAVE_DATA, d, slave_len=3)
        if r[2] != (field_id & 0xFF) or r[3] != (offset & 0xFF) or r[4] != len(data):
            raise HiperfaceError("Echoed field/offset/length do not match request")
        return True

    @staticmethod
    def decode_field_status(st):
        """Status byte of 4Ch / 4Dh."""
        return {"size": ((st & 0x07) + 1) * 16, "code_enabled": bool(st & 0x08), "code_idx": (st >> 4) & 0x03,
                "writable": bool(st & 0x40), "exists": bool(st & 0x80)}

    @staticmethod
    def build_field_status(size, code_idx=0, code_enabled=True, write_enabled=True, exists=True):
        if size % 16 != 0 or not (16 <= size <= 128):
            raise HiperfaceError("Size must be a multiple of 16 between 16 and 128")
        st = ((size // 16) - 1) & 0x07
        if code_enabled:
            st |= 0x08                       # bit 3: 1 = access code enabled
        st |= (code_idx & 0x03) << 4         # bits 4..5: linked access code Code0..Code3
        if write_enabled:
            st |= 0x40                       # bit 6: 1 = write-enabled, 0 = read-only
        if exists:
            st |= 0x80                       # bit 7: 1 = create/modify, 0 = delete
        return st

    def data_status(self, field_id):
        r = self._send_cmd(self.CMD_DATA_STATUS, bytes([field_id & 0xFF]), slave_len=2)
        if r[2] != (field_id & 0xFF):
            raise HiperfaceError("Echoed field number does not match request")
        return r[3]

    def create_field(self, field_id, size, access_code_idx=0, write_enabled=True, code_enabled=True,
                     access_code=None):
        """4Dh: [field][status][access code]. The access code byte must be the value of the linked code,
        even when the code is disabled for that field."""
        status = self.build_field_status(size, access_code_idx, code_enabled, write_enabled, True)
        ac = self.code0 if access_code is None else access_code
        self._send_cmd(self.CMD_CREATE_FIELD, bytes([field_id & 0xFF, status, ac & 0xFF]))
        return status

    def delete_field(self, field_id, access_code=None):
        """4Dh with bit 7 = 0. Only the last (highest) data field can be deleted."""
        cur = self.data_status(field_id)
        status = cur & 0x7F
        ac = self.code0 if access_code is None else access_code
        self._send_cmd(self.CMD_CREATE_FIELD, bytes([field_id & 0xFF, status, ac & 0xFF]))
        return status

    def read_memory(self):
        """4Eh: [free 16-byte blocks][number of data fields]"""
        r = self._send_cmd(self.CMD_READ_MEM, slave_len=2)
        return r[2] * 16, r[3]

    def change_access_key(self, code_num, old_key, new_key):
        """4Fh: [code number][old][new] -> [code number]"""
        if not (0 <= code_num <= 3):
            raise HiperfaceError("Code number must be 0..3")
        if not (0 <= old_key <= 255 and 0 <= new_key <= 255):
            raise HiperfaceError("Keys must be 0x00..0xFF")
        r = self._send_cmd(self.CMD_CHANGE_ACCESS, bytes([code_num, old_key, new_key]), slave_len=1)
        if r[2] != code_num:
            raise HiperfaceError("Echoed code number does not match request")
        return True

    def read_status(self):
        """50h: one entry of the Slave error stack (00h = nothing active)."""
        r = self._send_cmd(self.CMD_READ_STATUS, slave_len=1)
        return r[2]

    def read_status_stack(self, limit=5):
        """Read 50h until 00h. The Slave stores up to 4 codes; each must be read separately."""
        codes = []
        for _i in range(limit):
            c = self.read_status()
            if c == 0:
                break
            codes.append(c)
            if not self.warning:
                break
        return codes

    @classmethod
    def describe_uart(cls, b):
        baud = BAUD_MAP.get(b & 0x07, "?")
        parity = {0: "no parity", 2: "even parity", 3: "odd parity"}.get((b >> 4) & 0x03, "?")
        tmo = "5x" if b & 0x40 else "2x"
        mode = "standard slave" if b & 0x80 else "bus slave"
        return "%s baud, %s, timeout %s, %s" % (baud, parity, tmo, mode)

    def read_type_label(self):
        """52h: [UART settings][encoder type][EEPROM size /16][options]"""
        r = self._send_cmd(self.CMD_READ_TYPE, slave_len=4)
        return {"uart": r[2], "type": r[3], "mem_bytes": r[4] * 16, "option": r[5]}

    def read_extended_type_label(self):
        """Extended Type Label = read-only data field FFh, min. 64 bytes, readable with 4Ah."""
        d = self.read_data(self.EXT_TYPE_FIELD, 0, 64, self.code0)
        return decode_ext_type_label(d)

    def reset(self, post_wait=None):
        """53h: no response. The Slave restarts: 100..200 ms init, then default settings until ~900 ms,
        user-defined settings after 1100 ms (spec 2.4.1)."""
        self._send_cmd(self.CMD_RESET, wait_response=False)
        target = self.pending_uart
        if target is not None:
            try:
                apply_uart_to_port(self.ser, target)
            except Exception:
                pass
            self.pending_uart = None
        if post_wait is None:
            default = (self._baud() == 9600 and getattr(self.ser, "parity", "E") == "E")
            post_wait = 0.25 if default else 1.2
        time.sleep(post_wait)
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass
        self.warning = False
        self._last_io = time.time()
        return target

    def sensor_adjustment(self, option_code):
        """6Bh (optional, product specific): [option][Code0]. Returns the Slave data bytes."""
        r = self._send_cmd(self.CMD_SENSOR_ADJUST, bytes([option_code & 0xFF, self.code0 & 0xFF]))
        return self._data(r)

    def temp_config_serial(self, settings_byte):
        """67h (optional): new settings are used right after the response, which still uses the old ones.
        The PC port is switched to the new settings here as well."""
        uart_to_port(settings_byte)
        r = self._send_cmd(self.CMD_TEMP_SET_SERIAL, bytes([settings_byte & 0xFF]), slave_len=1)
        apply_uart_to_port(self.ser, settings_byte)
        self._last_io = time.time()
        return r[2]

    def set_position_sync(self, value):
        """6Ah (optional): preset + Code0, synchronised to the sin/cos phase. Returns the value used."""
        d = struct.pack(">I", value & 0xFFFFFFFF) + bytes([self.code0 & 0xFF])
        r = self._send_cmd(self.CMD_SET_POS_SYNC, d)
        data = self._data(r)
        if len(data) >= 4:
            return struct.unpack(">I", data[:4])[0]
        return None

    def read_sync_offset(self):
        """6Ch (optional). Returns the Slave data bytes."""
        r = self._send_cmd(self.CMD_READ_SYNC_OFFSET)
        return self._data(r)

    def allocate_address(self, new_addr):
        """55h: [new address][Code0]. The response already comes from the new address (spec Table 30)."""
        if not (0x40 <= new_addr <= 0x5F):
            raise HiperfaceError("New address must be 0x40..0x5F")
        self._send_cmd(self.CMD_ALLOC_ADDR, bytes([new_addr, self.code0 & 0xFF]), slave_len=0,
                       resp_addr=new_addr)
        self.addr = new_addr
        return True

    def read_serial_version(self):
        """56h: 37 bytes = serial no. (9) + firmware version (20) + firmware date (8), ASCII."""
        r = self._send_cmd(self.CMD_READ_SERIAL_VER)
        d = self._data(r)
        dec = lambda b: b.decode("ascii", "ignore").strip("\x00 ")
        if len(d) >= 37:
            return dec(d[0:9]), dec(d[9:29]), dec(d[29:37])
        if len(d) >= 17:
            return dec(d[0:9]), dec(d[9:-8]), dec(d[-8:])
        raise HiperfaceError("Version response too short (%d data bytes)" % len(d))

    def config_serial(self, settings_byte, access_code=None):
        """57h: [UART settings][Code0] -> [UART settings]. Active only after 53h or a power cycle."""
        uart_to_port(settings_byte)
        ac = self.code0 if access_code is None else access_code
        r = self._send_cmd(self.CMD_CONFIG_SERIAL, bytes([settings_byte & 0xFF, ac & 0xFF]), slave_len=1)
        self.pending_uart = settings_byte & 0xFF
        return r[2]

    def send_raw(self, payload, append_crc=True, read_len=0):
        pkt = bytearray(payload)
        if append_crc:
            pkt.append(self.crc(pkt))
        self._pause()
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass
        self.ser.write(bytes(pkt))
        self._emit("TX", pkt)
        cmd = pkt[1] & 0x7F if len(pkt) > 1 else 0
        tmo = (RESPONSE_TIME_MS.get(cmd, 250) / 1000.0 + (len(pkt) + 140) * self.char_time()
               + self.timeout_condition() * 2 + self.margin)
        r = self._read_frame(read_len if read_len > 0 else None, -1, tmo)
        self._last_io = time.time()
        if r:
            self._emit("RX", r)
        return bytes(r)


def decode_ext_type_label(d):
    """Extended Type Label layout (spec, data field FFh)."""
    d = bytes(d)
    out = {"raw": d}
    if len(d) < 0x1E:
        return out
    x = 0
    for b in bytearray(d[1:]):
        x ^= b
    t = d[1]
    out.update({
        "checksum": d[0], "checksum_calc": x,
        "linear": bool(t & 0x01), "bipolar": bool(t & 0x02),
        "resolution": struct.unpack(">I", d[2:6])[0],
        "range": struct.unpack(">I", d[6:10])[0],
        "designation": d[0x0A:0x1C].split(b"\x00")[0].decode("ascii", "ignore").strip(),
        "selector": struct.unpack(">H", d[0x1C:0x1E])[0],
    })
    return out


# =============================================================================
#  Simulated encoder (demo mode, lets you try the UI without hardware)
# =============================================================================
def _sim_ext_label():
    d = bytearray(64)
    d[1] = 0x00                                     # rotary, unipolar
    d[2:6] = struct.pack(">I", 1024)                # periods / turn
    d[6:10] = struct.pack(">I", 4096)               # coded revolutions
    name = b"SRM50-DEMO"
    d[0x0A:0x0A + len(name)] = name
    d[0x1C:0x1E] = struct.pack(">H", 0x0001)        # temperature channel available
    d[0x1E] = 0x48
    x = 0
    for b in d[1:]:
        x ^= b
    d[0] = x
    return d


class SimulatedEncoderSerial(object):
    """Behaves like an SRM50 on the bus: XOR checksum, error frames, warning bit, data fields with access
    codes, 50h error stack, address/UART changes and the reset state machine (simplified)."""

    def __init__(self, baudrate=9600, parity="E"):
        self.port = "DEMO"
        self.is_open = True
        self.baudrate = baudrate
        self.parity = parity
        self._active = (baudrate, parity)     # settings the simulated slave is listening with
        self._rx = bytearray()
        self.addr = 0x40
        self.offset = 0
        self.counter = 1234
        self.uart = 0xE4
        self.codes = [0x55, 0x55, 0x55, 0x55]
        self.t0 = time.time()
        self.fields = [{"st": 0xC9, "data": bytearray(b"HIPERFACE-DEMO".ljust(32, b"\x00"))}]   # 32 B, Code0
        self.ext = _sim_ext_label()
        self.errors = []                       # pending warnings (error stack)
        self.total_blocks = 112                # 1792 bytes user memory

    # --- pyserial-like API
    @property
    def in_waiting(self):
        return len(self._rx)

    def _pos(self):
        return (int((time.time() - self.t0) * 4000) + self.offset) & 0xFFFFFFFF

    def reset_input_buffer(self):
        self._rx = bytearray()

    def reset_output_buffer(self):
        pass

    def flush(self):
        pass

    def close(self):
        self.is_open = False

    def read(self, n=1):
        out = bytes(self._rx[:n])
        self._rx = self._rx[n:]
        return out

    def inject_warning(self, code):
        if code not in self.errors:
            self.errors.append(code)
        del self.errors[:-4]

    # --- slave side
    def _reply(self, cmd, data=b"", addr=None):
        c = cmd | (0x80 if self.errors else 0)
        f = bytearray([self.addr if addr is None else addr, c]) + bytearray(data)
        f.append(HiperfaceEncoder.crc(f))
        self._rx += f

    def _err(self, code):
        self._reply(0x50, bytes([code]))
        return None

    def _used_blocks(self):
        return sum((f["st"] & 7) + 1 for f in self.fields)

    def write(self, pkt):
        pkt = bytearray(pkt)
        time.sleep(0.003)
        if (self.baudrate, self.parity) != self._active:
            return len(pkt)                    # garbage for the slave: no answer
        if len(pkt) < 3 or pkt[0] not in (self.addr, 0xFF):
            return len(pkt)
        if HiperfaceEncoder.crc(pkt[:-1]) != pkt[-1]:
            self._err(0x0A)
            return len(pkt)
        self._handle(pkt[1], pkt[2:-1])
        return len(pkt)

    def _handle(self, cmd, a):
        n = len(a)
        need = {0x42: 0, 0x43: 5, 0x44: 1, 0x46: 0, 0x47: 0, 0x49: 1, 0x4C: 1, 0x4D: 3, 0x4E: 0, 0x4F: 3,
                0x50: 0, 0x52: 0, 0x53: 0, 0x55: 2, 0x56: 0, 0x57: 2, 0x67: 1, 0x6A: 5, 0x6B: 2, 0x6C: 0}
        if cmd in need and n != need[cmd]:
            return self._err(0x0C)
        if cmd == 0x42:
            self._reply(cmd, struct.pack(">I", self._pos()))
        elif cmd in (0x43, 0x6A):
            if a[4] != self.codes[0]:
                return self._err(0x0F)
            want = struct.unpack(">I", bytes(a[:4]))[0]
            if cmd == 0x6A:
                want = (want // 32) * 32
            cur = int((time.time() - self.t0) * 4000)
            self.offset = want - cur
            self._reply(cmd, struct.pack(">I", want) if cmd == 0x6A else b"")
        elif cmd == 0x44:
            if a[0] == 0x48:
                self._reply(cmd, bytes([a[0]]) + struct.pack(">h", 37))
            else:
                return self._err(0x0D)
        elif cmd == 0x46:
            self._reply(cmd, struct.pack(">I", self.counter)[1:])
        elif cmd == 0x47:
            if self.counter >= 0xFFFFFF:
                return self._err(0x08)
            self.counter += 1
            self._reply(cmd)
        elif cmd == 0x49:
            if a[0] != self.codes[0]:
                return self._err(0x0F)
            self.counter = 0
            self._reply(cmd)
        elif cmd in (0x4A, 0x4B):
            if n < 4 or (cmd == 0x4A and n != 4) or (cmd == 0x4B and n != 4 + a[2]):
                return self._err(0x0C)
            fid, off, cnt, ac = a[0], a[1], a[2], a[3]
            if not (1 <= cnt <= 128):
                return self._err(0x0D)
            if fid == 0xFF:
                if cmd == 0x4B:
                    return self._err(0x0E)
                buf, st = self.ext, 0x03
            elif fid < len(self.fields):
                buf, st = self.fields[fid]["data"], self.fields[fid]["st"]
            else:
                return self._err(0x12)
            if fid != 0xFF and st & 0x08 and ac != self.codes[(st >> 4) & 3]:
                return self._err(0x0F)
            if off + cnt > len(buf):
                return self._err(0x11)
            if cmd == 0x4A:
                self._reply(cmd, bytes([fid, off, cnt]) + bytes(buf[off:off + cnt]))
            else:
                if not st & 0x40:
                    return self._err(0x0E)
                buf[off:off + cnt] = a[4:4 + cnt]
                self._reply(cmd, bytes([fid, off, cnt]))
        elif cmd == 0x4C:
            fid = a[0]
            if fid == 0xFF:
                return self._reply(cmd, bytes([fid, 0x83]))
            if fid >= len(self.fields):
                return self._err(0x12)
            self._reply(cmd, bytes([fid, self.fields[fid]["st"]]))
        elif cmd == 0x4D:
            fid, st, ac = a[0], a[1], a[2]
            if ac != self.codes[(st >> 4) & 3]:
                return self._err(0x0F)
            last = len(self.fields) - 1
            if fid == len(self.fields):                       # create next field
                if not st & 0x80:
                    return self._err(0x12)
                if self._used_blocks() + (st & 7) + 1 > self.total_blocks:
                    return self._err(0x10)
                self.fields.append({"st": st, "data": bytearray(((st & 7) + 1) * 16)})
            elif fid <= last:
                f = self.fields[fid]
                if not st & 0x80:                              # delete
                    if fid != last:
                        return self._err(0x10)
                    self.fields.pop()
                elif (st & 7) != (f["st"] & 7):                 # size change
                    if fid != last or (st & 7) < (f["st"] & 7):
                        return self._err(0x10)
                    f["data"] = f["data"].ljust(((st & 7) + 1) * 16, b"\x00")
                    f["st"] = st
                else:
                    f["st"] = st
            else:
                return self._err(0x12)
            self._reply(cmd, bytes([fid, st]))
        elif cmd == 0x4E:
            self._reply(cmd, bytes([self.total_blocks - self._used_blocks(), len(self.fields)]))
        elif cmd == 0x4F:
            num, old, new = a[0], a[1], a[2]
            if num > 3:
                return self._err(0x0D)
            if old != self.codes[num]:
                return self._err(0x0F)
            self.codes[num] = new
            self._reply(cmd, bytes([num]))
        elif cmd == 0x50:
            code = self.errors.pop(0) if self.errors else 0x00
            self._reply(cmd, bytes([code]))
        elif cmd == 0x52:
            self._reply(cmd, bytes([self.uart, 0x27, 0x10, 0x00]))
        elif cmd == 0x53:
            self.errors = []
            self._active = uart_to_port(self.uart)
        elif cmd == 0x55:
            if a[1] != self.codes[0]:
                return self._err(0x0F)
            if not (0x40 <= a[0] <= 0x5F):
                return self._err(0x0D)
            self.addr = a[0]
            self._reply(cmd)
        elif cmd == 0x56:
            self._reply(cmd, b"123456789" + b"SRM50 FW 1.42".ljust(20, b"\x00") + b"10.03.16")
        elif cmd == 0x57:
            if a[1] != self.codes[0]:
                return self._err(0x0F)
            try:
                uart_to_port(a[0])
            except ValueError:
                return self._err(0x0D)
            self.uart = a[0]
            self._reply(cmd, bytes([a[0]]))
        elif cmd == 0x67:
            try:
                new = uart_to_port(a[0])
            except ValueError:
                return self._err(0x0D)
            self._reply(cmd, bytes([a[0]]))
            self._active = new
        elif cmd == 0x6B:
            if a[1] != self.codes[0]:
                return self._err(0x0F)
            self._reply(cmd, bytes([a[0], 0x00]))
        elif cmd == 0x6C:
            self._reply(cmd, bytes([(self._pos() + 7) & 0x1F]))
        else:
            return self._err(0x0B)
        return None


# =============================================================================
#  Helpers
# =============================================================================
def parse_int(text, hex_default=False):
    s = str(text).strip().replace("_", "")
    if not s:
        raise ValueError("empty value")
    low = s.lower()
    if low.endswith("h"):
        return int(low[:-1], 16)
    if low.startswith(("0x", "0b", "0o")):
        return int(low, 0)
    return int(low, 16 if hex_default else 10)


def parse_hex_bytes(text):
    s = str(text).replace("0x", "").replace("0X", "").replace(",", " ").replace(" ", "")
    if len(s) % 2:
        raise ValueError("hex string needs an even number of digits")
    return bytes.fromhex(s)


def hex_spaced(b):
    return " ".join("%02X" % x for x in bytearray(b))


def resource_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def settings_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "HiperfaceStudio")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, "settings.json")


def enable_dpi_awareness():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)   # Win 8.1+
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()        # Win 7
    except Exception:
        pass


# =============================================================================
#  Worker thread: all serial I/O happens here, UI never freezes
# =============================================================================
class Worker(threading.Thread):
    def __init__(self, ui_queue):
        threading.Thread.__init__(self, daemon=True)
        self.jobs = queue.Queue()
        self.ui = ui_queue
        self.quiet = False

    def submit(self, label, fn, on_ok=None, quiet=False):
        self.jobs.put((label, fn, on_ok, quiet))

    def run(self):
        while True:
            job = self.jobs.get()
            if job is None:
                break
            label, fn, on_ok, quiet = job
            self.quiet = quiet
            try:
                res = fn()
                self.ui.put(("ok", label, res, on_ok, quiet))
            except Exception as e:
                self.ui.put(("err", label, e, None, quiet))
            finally:
                self.quiet = False




# =============================================================================
#  Extras: Persian fault texts, UART description, PDF lookup
# =============================================================================
FAULT_CODES_FA = {
    0x00: "بدون خطا (سالم)",
    0x01: "سیگنال‌های آنالوگ خارج از محدوده",
    0x02: "افست زاویه داخلی نادرست",
    0x03: "جدول پارتیشن‌بندی فیلد داده خراب",
    0x04: "مقادیر حد آنالوگ در دسترس نیست",
    0x05: "باس I2C داخلی غیرفعال",
    0x06: "خطای چک‌سام داخلی",
    0x07: "ریست توسط واچ‌داگ برنامه",
    0x08: "سرریز شمارنده",
    0x09: "خطای پریتی",
    0x0A: "خطای چک‌سام داده‌ی ارسالی",
    0x0B: "دستور ناشناخته",
    0x0C: "طول داده‌ی ارسالی اشتباه",
    0x0D: "آرگومان دستور مجاز نیست",
    0x0E: "فیلد داده فقط‌خواندنی است",
    0x0F: "کد دسترسی نادرست",
    0x10: "حافظه پر است / اندازه‌ی فیلد قابل تغییر نیست",
    0x11: "آفست خارج از محدوده‌ی فیلد",
    0x12: "فیلد داده وجود ندارد",
    0x1C: "هشدار پایش سیگنال آنالوگ",
    0x1D: "جریان فرستنده (LED) بحرانی",
    0x1E: "دمای انکودر بحرانی",
    0x1F: "سرعت بیش از حد مجاز",
    0x20: "موقعیت Singleturn نامطمئن / کالیبره نشده",
    0x21: "خطای دامنه Multiturn",
    0x22: "خطای همگام‌سازی Multiturn",
    0x23: "خطای طول بردار Multiturn",
    0x24: "خطای شمارنده Multiturn",
}


def fault_text(code, lang="en"):
    table = FAULT_CODES_FA if lang == "fa" else HiperfaceEncoder.FAULT_CODES
    return table.get(code, "کد خطای ناشناخته" if lang == "fa" else "Unknown fault code")


def describe_uart(b, lang="en"):
    baud = HiperfaceEncoder.BAUD_MAP.get(b & 0x07, "?")
    p = (b >> 4) & 0x03
    if lang == "fa":
        parity = {0: "بدون پریتی", 2: "پریتی زوج", 3: "پریتی فرد"}.get(p, "?")
        mode = "اسلیو استاندارد" if b & 0x80 else "اسلیو باس"
        return "%s باود، %s، تایم‌اوت %s، %s" % (baud, parity, "5x" if b & 0x40 else "2x", mode)
    return HiperfaceEncoder.describe_uart(b)


PDF_ONLINE = ("https://www.sick.com/media/docs/5/65/865/operating_instructions_specification_"
              "hiperface%C2%AE_motor_feedback_protocol_en_im0064865.pdf")
PDF_NAME = "operating_instructions_specification_hiperface\u00ae_motor_feedback_protocol_en_im0064865.pdf"
PDF_FALLBACK_DIR = r"D:\PMC\Downloads\Compressed\HiperfaceStudio"
# exact locations the developer uses (project root, plus the variant without a path separator)
PDF_FIXED_PATHS = [
    os.path.join(PDF_FALLBACK_DIR, PDF_NAME),
    PDF_FALLBACK_DIR + PDF_NAME,
]
REPO_URL = "https://github.com/morteza-taheri/HiperfaceStudio"
ISSUES_URL = REPO_URL + "/issues"
AUTHOR = "Morteza Taheri"
AUTHOR_FA = "مرتضی طاهری"
AUTHOR_EMAIL = "morteza.taheri@live.com"
VAZIR_URL = "https://github.com/rastikerdar/vazirmatn"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _is_spec_pdf(name):
    n = name.lower()
    return n.endswith(".pdf") and "im0064865" in n


def find_pdf(custom=None):
    """Order: path chosen by the user -> next to the EXE/script -> working dir -> copy bundled in the EXE ->
    D:\\PMC\\Downloads\\Compressed\\HiperfaceStudio (and its parent). Any PDF whose name contains
    'im0064865' is accepted."""
    if custom and os.path.isfile(custom):
        return custom
    for p in PDF_FIXED_PATHS:
        try:
            if os.path.isfile(p):
                return p
        except Exception:
            pass
    seen = []
    dirs = (app_dir(), os.getcwd(), resource_dir(), PDF_FALLBACK_DIR, os.path.dirname(PDF_FALLBACK_DIR))
    for d in dirs:
        if not d or d in seen or not os.path.isdir(d):
            continue
        seen.append(d)
        exact = os.path.join(d, PDF_NAME)
        if os.path.isfile(exact):
            return exact
        try:
            for f in sorted(os.listdir(d)):
                if _is_spec_pdf(f) and os.path.isfile(os.path.join(d, f)):
                    return os.path.join(d, f)
        except Exception:
            pass
    return None


def open_path_or_url(target):
    import webbrowser
    if os.path.isfile(target) and sys.platform == "win32":
        os.startfile(target)  # noqa
        return
    if os.path.isfile(target):
        webbrowser.open("file://" + os.path.abspath(target))
        return
    webbrowser.open(target)


# =============================================================================
#  Fonts: Vazirmatn / Vazir for Persian, loaded from ./fonts without installing
# =============================================================================
PERSIAN_FONTS = ["Vazirmatn", "Vazirmatn UI", "Vazirmatn FD", "Vazir", "Vazir FD", "Vazir Code"]
FONT_FALLBACK_FA = ["Tahoma", "Segoe UI", "Arial", "DejaVu Sans"]
_loaded_font_files = []


def font_dirs():
    out = []
    for d in (os.path.join(app_dir(), "fonts"), os.path.join(resource_dir(), "fonts"), app_dir(), resource_dir(),
              os.path.join(PDF_FALLBACK_DIR, "fonts")):
        if d not in out and os.path.isdir(d):
            out.append(d)
    return out


def find_font_files():
    files = []
    for d in font_dirs():
        try:
            for f in sorted(os.listdir(d)):
                if f.lower().endswith((".ttf", ".otf")) and "vazir" in f.lower():
                    p = os.path.join(d, f)
                    if p not in files:
                        files.append(p)
        except Exception:
            pass
    return files


def load_private_fonts():
    """Register the bundled Vazir font files for this process only (no admin rights, nothing installed).
    Must run before tk.Tk() so Tk sees the new families. Returns the list of loaded files."""
    files = find_font_files()
    if not files:
        return []
    if sys.platform == "win32":
        try:
            import ctypes
            gdi = ctypes.windll.gdi32
            FR_PRIVATE = 0x10
            for p in files:
                try:
                    if gdi.AddFontResourceExW(ctypes.c_wchar_p(p), FR_PRIVATE, 0):
                        _loaded_font_files.append(p)
                except Exception:
                    pass
        except Exception:
            pass
    else:
        try:
            import ctypes
            import ctypes.util
            name = ctypes.util.find_library("fontconfig")
            if name:
                fc = ctypes.CDLL(name)
                fc.FcConfigGetCurrent.restype = ctypes.c_void_p
                fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
                cfg = fc.FcConfigGetCurrent()
                for p in files:
                    if fc.FcConfigAppFontAddFile(cfg, p.encode("utf-8")):
                        _loaded_font_files.append(p)
        except Exception:
            pass
    return list(_loaded_font_files)
