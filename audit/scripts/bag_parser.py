"""
Minimal pure-Python ROS1 bag (V2.0) parser.

Extracts metadata, IMU statistics, odometry velocity profile, and PointCloud2
headers without requiring any ROS install. Only stdlib.

Bag format reference:
  http://wiki.ros.org/Bags/Format/2.0

Record structure: <4-byte header_len><header><4-byte data_len><data>
Header is sequence of <4-byte field_len><name=value> pairs.
Records of interest:
  op=0x05 connection: connection metadata (topic, type, md5, etc.)
  op=0x07 message data: a serialized message
  op=0x03 chunk: a (compressed or uncompressed) container of records
"""

from __future__ import annotations
import struct
import sys
import math
import bz2
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Iterator, Any


# ---------- low-level record reading -----------------------------------------

def _read_exact(f, n: int) -> bytes:
    buf = f.read(n)
    if len(buf) != n:
        raise EOFError(f"requested {n} bytes, got {len(buf)}")
    return buf


def _parse_header(blob: bytes) -> Dict[str, bytes]:
    out: Dict[str, bytes] = {}
    i = 0
    while i < len(blob):
        (field_len,) = struct.unpack_from("<I", blob, i)
        i += 4
        field = blob[i:i + field_len]
        i += field_len
        eq = field.index(b"=")
        out[field[:eq].decode()] = field[eq + 1:]
    return out


def _iter_records(stream) -> Iterator[Tuple[int, Dict[str, bytes], bytes]]:
    """Yield (op, header_dict, data) for each record in the stream."""
    while True:
        try:
            (header_len,) = struct.unpack("<I", _read_exact(stream, 4))
        except EOFError:
            return
        header_blob = _read_exact(stream, header_len)
        header = _parse_header(header_blob)
        (data_len,) = struct.unpack("<I", _read_exact(stream, 4))
        data = _read_exact(stream, data_len)
        op = header.get("op")
        op_int = op[0] if op else 0
        yield op_int, header, data


# ---------- ROS1 message field decoding helpers ------------------------------

def _decode_string(buf: bytes, off: int) -> Tuple[str, int]:
    (slen,) = struct.unpack_from("<I", buf, off)
    off += 4
    return buf[off:off + slen].decode("utf-8", errors="replace"), off + slen


def _decode_header(buf: bytes, off: int) -> Tuple[Tuple[int, int, str], int]:
    """std_msgs/Header: uint32 seq, time stamp (sec+nsec), string frame_id."""
    seq, sec, nsec = struct.unpack_from("<III", buf, off)
    off += 12
    frame_id, off = _decode_string(buf, off)
    return (seq, sec * 1_000_000_000 + nsec, frame_id), off


def _decode_imu(buf: bytes) -> Dict[str, Any]:
    """sensor_msgs/Imu."""
    off = 0
    (seq, ts_ns, frame_id), off = _decode_header(buf, off)
    # orientation: 4 doubles
    qx, qy, qz, qw = struct.unpack_from("<dddd", buf, off)
    off += 32
    # orientation covariance: 9 doubles (skip)
    off += 72
    # angular velocity: 3 doubles
    wx, wy, wz = struct.unpack_from("<ddd", buf, off)
    off += 24
    # ang vel covariance: 9 doubles (skip)
    off += 72
    # linear acceleration: 3 doubles
    ax, ay, az = struct.unpack_from("<ddd", buf, off)
    off += 24
    return {"ts_ns": ts_ns, "frame_id": frame_id,
            "ang_vel": (wx, wy, wz),
            "lin_accel": (ax, ay, az),
            "orientation": (qx, qy, qz, qw)}


def _decode_odometry(buf: bytes) -> Dict[str, Any]:
    """nav_msgs/Odometry."""
    off = 0
    (seq, ts_ns, frame_id), off = _decode_header(buf, off)
    child_frame_id, off = _decode_string(buf, off)
    # PoseWithCovariance: Pose (7 doubles) + 36 doubles cov = 43 doubles = 344 bytes
    px, py, pz, qx, qy, qz, qw = struct.unpack_from("<ddddddd", buf, off)
    off += 56
    off += 36 * 8  # covariance
    # TwistWithCovariance: Twist (6 doubles) + 36 doubles cov = 42 doubles = 336 bytes
    lx, ly, lz, ax, ay, az = struct.unpack_from("<dddddd", buf, off)
    off += 48
    off += 36 * 8
    return {"ts_ns": ts_ns, "frame_id": frame_id,
            "child_frame_id": child_frame_id,
            "position": (px, py, pz),
            "twist_linear": (lx, ly, lz),
            "twist_angular": (ax, ay, az),
            "speed_mps": math.sqrt(lx * lx + ly * ly + lz * lz)}


def _decode_pc2_header(buf: bytes) -> Dict[str, Any]:
    """sensor_msgs/PointCloud2 — only header + dimensions, NOT field data."""
    off = 0
    (seq, ts_ns, frame_id), off = _decode_header(buf, off)
    height, width = struct.unpack_from("<II", buf, off)
    off += 8
    # fields array
    (fields_count,) = struct.unpack_from("<I", buf, off)
    off += 4
    fields = []
    for _ in range(fields_count):
        name, off = _decode_string(buf, off)
        fld_off, datatype, count = struct.unpack_from("<IBI", buf, off)
        off += 9
        fields.append({"name": name, "offset": fld_off, "datatype": datatype, "count": count})
    is_bigendian, point_step, row_step = struct.unpack_from("<BII", buf, off)
    off += 9
    (data_len,) = struct.unpack_from("<I", buf, off)
    return {"ts_ns": ts_ns, "frame_id": frame_id,
            "height": height, "width": width,
            "n_points": height * width,
            "fields": [f["name"] for f in fields],
            "point_step": point_step, "data_bytes": data_len}


# ---------- bag traversal ----------------------------------------------------

@dataclass
class Connection:
    conn_id: int
    topic: str
    msg_type: str


@dataclass
class TopicStats:
    topic: str
    msg_type: str
    count: int = 0
    first_ts_ns: Optional[int] = None
    last_ts_ns: Optional[int] = None
    frame_ids: set = field(default_factory=set)
    # per-message-type extras populated by callers
    imu_records: List[Dict[str, Any]] = field(default_factory=list)
    odom_records: List[Dict[str, Any]] = field(default_factory=list)
    pc2_records: List[Dict[str, Any]] = field(default_factory=list)


def parse_bag(path: str, full_imu_odom: bool = True) -> Dict[str, TopicStats]:
    """
    Stream-parse a ROS1 V2.0 bag and return per-topic statistics.

    full_imu_odom=True: keep every IMU and odometry sample (memory cost
    is ~80 bytes/sample, manageable).
    PointCloud2 records: only header decoded, not point data.
    """
    connections: Dict[int, Connection] = {}
    topics: Dict[str, TopicStats] = {}

    def handle_message(conn_id: int, ts_ns: int, data: bytes) -> None:
        conn = connections.get(conn_id)
        if conn is None:
            return
        ts = topics.setdefault(conn.topic, TopicStats(conn.topic, conn.msg_type))
        ts.count += 1
        ts.first_ts_ns = ts_ns if ts.first_ts_ns is None else min(ts.first_ts_ns, ts_ns)
        ts.last_ts_ns = ts_ns if ts.last_ts_ns is None else max(ts.last_ts_ns, ts_ns)
        # Selective decoding by message type
        if conn.msg_type == "sensor_msgs/Imu" and full_imu_odom:
            try:
                rec = _decode_imu(data)
            except Exception:
                return
            ts.frame_ids.add(rec["frame_id"])
            ts.imu_records.append(rec)
        elif conn.msg_type == "nav_msgs/Odometry" and full_imu_odom:
            try:
                rec = _decode_odometry(data)
            except Exception:
                return
            ts.frame_ids.add(rec["frame_id"])
            ts.odom_records.append(rec)
        elif conn.msg_type == "sensor_msgs/PointCloud2":
            try:
                rec = _decode_pc2_header(data)
            except Exception:
                return
            ts.frame_ids.add(rec["frame_id"])
            ts.pc2_records.append(rec)

    with open(path, "rb") as f:
        # Skip the bag version line "#ROSBAG V2.0\n"
        first = f.readline()
        if not first.startswith(b"#ROSBAG"):
            raise ValueError(f"not a ROS1 bag: {path}")

        # ROS1 bag V2 op codes (corrected):
        #   0x02 = MESSAGE_DATA
        #   0x03 = BAG_HEADER
        #   0x04 = INDEX_DATA
        #   0x05 = CHUNK
        #   0x06 = CHUNK_INFO
        #   0x07 = CONNECTION
        for op, header, data in _iter_records(f):
            if op == 0x07:  # connection
                (conn_id,) = struct.unpack("<I", header["conn"])
                topic = header["topic"].decode()
                meta = _parse_header(data)
                msg_type = meta.get("type", b"").decode()
                connections[conn_id] = Connection(conn_id, topic, msg_type)
            elif op == 0x02:  # message data (top-level; rare in V2)
                (conn_id,) = struct.unpack("<I", header["conn"])
                (ts_ns,) = struct.unpack("<q", header["time"])
                handle_message(conn_id, ts_ns, data)
            elif op == 0x05:  # chunk
                comp = header.get("compression", b"none")
                if comp == b"bz2":
                    inner = bz2.decompress(data)
                elif comp == b"none":
                    inner = data
                else:
                    continue
                import io
                bio = io.BytesIO(inner)
                for iop, ih, idata in _iter_records(bio):
                    if iop == 0x07:  # connection in chunk
                        (conn_id,) = struct.unpack("<I", ih["conn"])
                        topic = ih["topic"].decode()
                        meta = _parse_header(idata)
                        msg_type = meta.get("type", b"").decode()
                        connections[conn_id] = Connection(conn_id, topic, msg_type)
                    elif iop == 0x02:  # message data in chunk
                        (conn_id,) = struct.unpack("<I", ih["conn"])
                        (ts_ns,) = struct.unpack("<q", ih["time"])
                        handle_message(conn_id, ts_ns, idata)

    return topics


# ---------- statistics helpers -----------------------------------------------

def imu_stats(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not recs:
        return {}
    n = len(recs)
    timestamps = [r["ts_ns"] for r in recs]
    timestamps.sort()
    duration_s = (timestamps[-1] - timestamps[0]) / 1e9
    rate_hz = (n - 1) / duration_s if duration_s > 0 else 0.0
    # Gap analysis
    gaps_ns = [timestamps[i + 1] - timestamps[i] for i in range(n - 1)]
    if gaps_ns:
        median_gap = sorted(gaps_ns)[len(gaps_ns) // 2]
        max_gap = max(gaps_ns)
        gap_anomalies = sum(1 for g in gaps_ns if g > 3 * median_gap)
    else:
        median_gap = max_gap = 0
        gap_anomalies = 0

    # Acceleration magnitude (should be ~9.81 m/s^2 if stationary)
    accel_mags = [math.sqrt(r["lin_accel"][0]**2 + r["lin_accel"][1]**2 + r["lin_accel"][2]**2) for r in recs]
    accel_mean = sum(accel_mags) / n
    accel_std = math.sqrt(sum((a - accel_mean) ** 2 for a in accel_mags) / n)

    # Gyro magnitude (should be ~0 if stationary)
    gyro_mags = [math.sqrt(r["ang_vel"][0]**2 + r["ang_vel"][1]**2 + r["ang_vel"][2]**2) for r in recs]
    gyro_mean = sum(gyro_mags) / n
    gyro_max = max(gyro_mags)

    return {
        "count": n,
        "duration_s": duration_s,
        "rate_hz": rate_hz,
        "median_gap_ms": median_gap / 1e6,
        "max_gap_ms": max_gap / 1e6,
        "gap_anomalies_3x": gap_anomalies,
        "accel_mag_mean": accel_mean,
        "accel_mag_std": accel_std,
        "gyro_mag_mean": gyro_mean,
        "gyro_mag_max": gyro_max,
    }


def odom_stats(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not recs:
        return {}
    speeds = [r["speed_mps"] for r in recs]
    n = len(speeds)
    return {
        "count": n,
        "speed_min": min(speeds),
        "speed_max": max(speeds),
        "speed_mean": sum(speeds) / n,
        "stationary_pct": 100.0 * sum(1 for s in speeds if s < 0.05) / n,
        "duration_s": (recs[-1]["ts_ns"] - recs[0]["ts_ns"]) / 1e9,
    }


# ---------- main: per-bag report ---------------------------------------------

def main(paths: List[str]) -> None:
    print("=" * 80)
    for path in paths:
        print(f"\n# {path}\n")
        try:
            topics = parse_bag(path)
        except Exception as e:
            print(f"  ERROR parsing: {e}")
            continue

        # Filter out high-noise topics, focus on perception-relevant ones
        focus = sorted(t for t in topics if any(k in t for k in
                       ["livox", "imu", "odom", "points"]))
        for topic in focus:
            ts = topics[topic]
            duration = (ts.last_ts_ns - ts.first_ts_ns) / 1e9 if ts.last_ts_ns else 0
            rate = (ts.count - 1) / duration if duration > 0 else 0
            print(f"  {topic}")
            print(f"    type: {ts.msg_type}")
            print(f"    count: {ts.count}    rate: {rate:.2f} Hz    duration: {duration:.2f} s")
            print(f"    frame_ids: {sorted(ts.frame_ids)}")
            if ts.imu_records:
                stats = imu_stats(ts.imu_records)
                print(f"    IMU: |a|={stats['accel_mag_mean']:.3f}±{stats['accel_mag_std']:.3f} m/s² "
                      f"|g|={stats['gyro_mag_mean']:.4f}/{stats['gyro_mag_max']:.4f} rad/s "
                      f"gap_med={stats['median_gap_ms']:.2f}ms gap_max={stats['max_gap_ms']:.2f}ms "
                      f"anom={stats['gap_anomalies_3x']}")
            if ts.odom_records:
                stats = odom_stats(ts.odom_records)
                print(f"    ODOM: speed [{stats['speed_min']:.3f},{stats['speed_max']:.3f}] mean={stats['speed_mean']:.3f} "
                      f"stationary={stats['stationary_pct']:.1f}%")
            if ts.pc2_records:
                widths = [r["n_points"] for r in ts.pc2_records]
                fields = ts.pc2_records[0]["fields"]
                print(f"    PC2: n_points min/median/max = "
                      f"{min(widths)}/{sorted(widths)[len(widths)//2]}/{max(widths)}, "
                      f"fields={fields}")


if __name__ == "__main__":
    main(sys.argv[1:])
