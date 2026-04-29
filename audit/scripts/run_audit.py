"""
Cross-bag audit. Runs bag_parser on every bag in ~/bags/, computes
statistics, and identifies anomalies relevant to the preprocessing
pipeline's correctness.

Outputs a structured findings doc at audit/notes/cross_bag_audit.md.
"""

from __future__ import annotations
import os
import sys
import glob
import time
import math
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bag_parser import parse_bag, imu_stats, odom_stats, TopicStats


def topic_kind(t: str) -> str:
    """Identify the role of a topic for our pipeline."""
    if "/livox_" in t and t.endswith("/imu"):
        return "lidar_imu"
    if "/livox_" in t and t.endswith("/points"):
        return "lidar_points"
    if t.endswith("/odom") and "/relative" not in t and "/navsat" not in t:
        return "primary_odom"
    return "other"


def lidar_name(topic: str) -> str:
    """Extract 'livox_front' from '/nbuggy/livox_front/{points,imu}'."""
    parts = topic.split("/")
    for i, p in enumerate(parts):
        if p.startswith("livox_") and i + 1 < len(parts):
            return p
    return ""


def per_lidar_summary(topics: Dict[str, TopicStats]) -> Dict[str, Dict[str, Any]]:
    """Group topics by lidar, return {lidar_name: {has_points, has_imu, ...}}."""
    out: Dict[str, Dict[str, Any]] = {}
    for tname, ts in topics.items():
        kind = topic_kind(tname)
        if kind == "lidar_imu":
            ln = lidar_name(tname)
            out.setdefault(ln, {})["has_imu"] = True
            out[ln]["imu_topic"] = tname
            out[ln]["imu_count"] = ts.count
            out[ln]["imu_frame_ids"] = sorted(ts.frame_ids)
            if ts.imu_records:
                out[ln]["imu_stats"] = imu_stats(ts.imu_records)
        elif kind == "lidar_points":
            ln = lidar_name(tname)
            out.setdefault(ln, {})["has_points"] = True
            out[ln]["points_topic"] = tname
            out[ln]["points_count"] = ts.count
            out[ln]["points_frame_ids"] = sorted(ts.frame_ids)
            if ts.pc2_records:
                widths = [r["n_points"] for r in ts.pc2_records]
                out[ln]["points_min"] = min(widths)
                out[ln]["points_med"] = sorted(widths)[len(widths) // 2]
                out[ln]["points_max"] = max(widths)
                out[ln]["points_fields"] = ts.pc2_records[0]["fields"]
                # cross-check: imu and points frames match?
                out[ln]["points_first_ts_ns"] = ts.pc2_records[0]["ts_ns"]
                out[ln]["points_last_ts_ns"] = ts.pc2_records[-1]["ts_ns"]
    # Mark missing companions
    for ln, info in out.items():
        info["has_imu"] = info.get("has_imu", False)
        info["has_points"] = info.get("has_points", False)
    return out


def odom_summary(topics: Dict[str, TopicStats]) -> Dict[str, Any]:
    """Find the primary /<ns>/odom topic and analyze."""
    for tname, ts in topics.items():
        if topic_kind(tname) == "primary_odom":
            return {"topic": tname,
                    "frame_ids": sorted(ts.frame_ids),
                    **(odom_stats(ts.odom_records) if ts.odom_records else {})}
    return {}


def cross_check(per_lidar: Dict[str, Dict[str, Any]],
                odom: Dict[str, Any]) -> List[str]:
    """Generate human-readable findings."""
    notes: List[str] = []

    # Per-lidar: each lidar with /points should also have /imu (preprocessing requires it).
    for ln, info in sorted(per_lidar.items()):
        if info["has_points"] and not info["has_imu"]:
            notes.append(f"  - {ln}: HAS /points but MISSING /imu — preprocessing would refuse to start.")
        if info["has_imu"] and not info["has_points"]:
            notes.append(f"  - {ln}: has /imu but no /points (sensor publishing IMU only?)")
        if info["has_imu"] and info["has_points"]:
            pf = info.get("points_frame_ids", [])
            if_ = info.get("imu_frame_ids", [])
            if pf != if_:
                notes.append(f"  - {ln}: frame_id mismatch: points={pf} imu={if_}")
            stats = info.get("imu_stats", {})
            if stats:
                # IMU sample rate sanity (Livox IMU is ~200 Hz)
                if stats["rate_hz"] < 50:
                    notes.append(f"  - {ln}: low IMU rate ({stats['rate_hz']:.1f} Hz)")
                if stats["max_gap_ms"] > 50:
                    notes.append(f"  - {ln}: IMU gap up to {stats['max_gap_ms']:.1f} ms (rate={stats['rate_hz']:.1f} Hz)")
                # Stationary acceleration check
                if abs(stats["accel_mag_mean"] - 9.81) > 0.5:
                    notes.append(f"  - {ln}: |accel| mean = {stats['accel_mag_mean']:.3f} m/s² (expected ~9.81)")
                # Gap anomalies
                if stats["gap_anomalies_3x"] > stats["count"] * 0.01:
                    notes.append(f"  - {ln}: {stats['gap_anomalies_3x']} IMU gaps > 3× median (out of {stats['count']})")

    # Odom: stationary period should exist for calibration to complete.
    if odom and "speed_min" in odom:
        if odom["speed_min"] > 0.05:
            notes.append(f"  - odom: never below 0.05 m/s (min={odom['speed_min']:.3f}); calibration would never complete in this bag")
        if odom.get("stationary_pct", 0) < 5:
            notes.append(f"  - odom: <5% stationary ({odom['stationary_pct']:.1f}%); calibration window unlikely to fit")

    return notes


def fmt_bag_section(path: str) -> str:
    out: List[str] = []
    bag_name = os.path.basename(path)
    out.append(f"## {bag_name}")
    t0 = time.time()
    try:
        topics = parse_bag(path)
    except Exception as e:
        return f"## {bag_name}\n\nPARSE ERROR: {e}\n"
    elapsed = time.time() - t0

    per_lidar = per_lidar_summary(topics)
    odom = odom_summary(topics)
    notes = cross_check(per_lidar, odom)

    out.append("")
    out.append(f"_(parsed in {elapsed:.1f}s)_")
    out.append("")
    out.append("### Per-lidar inventory")
    out.append("")
    out.append("| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |")
    out.append("|---|---|---|---|---|---|---|---|")
    for ln in sorted(per_lidar):
        info = per_lidar[ln]
        if info.get("points_med"):
            pts = f"{info['points_min']}/{info['points_med']}/{info['points_max']}"
        else:
            pts = "-"
        stats = info.get("imu_stats", {})
        rate = f"{stats['rate_hz']:.1f}" if stats else "-"
        amag = f"{stats['accel_mag_mean']:.2f}±{stats['accel_mag_std']:.2f}" if stats else "-"
        gmag = f"{stats['gyro_mag_mean']:.4f}/{stats['gyro_mag_max']:.4f}" if stats else "-"
        gap = f"{stats['max_gap_ms']:.1f}" if stats else "-"
        out.append(f"| {ln} | {'✓' if info['has_points'] else '—'} | {'✓' if info['has_imu'] else '—'} | {pts} | {rate} | {amag} | {gmag} | {gap} |")
    out.append("")

    if odom and "speed_max" in odom:
        out.append("### Odometry (`/<ns>/odom`)")
        out.append("")
        out.append(f"- topic: {odom['topic']}")
        out.append(f"- frame_ids: {odom['frame_ids']}")
        out.append(f"- speed: min={odom['speed_min']:.3f}, max={odom['speed_max']:.3f}, mean={odom['speed_mean']:.3f} m/s")
        out.append(f"- stationary (speed<0.05): {odom['stationary_pct']:.1f}% of {odom['count']} samples")
        out.append("")

    if notes:
        out.append("### ⚠ Findings")
        out.append("")
        out.extend(notes)
        out.append("")
    else:
        out.append("### Findings: clean")
        out.append("")

    return "\n".join(out)


def main():
    bag_dir = "/home/sutd_ubuntu20/bags"
    bags = sorted(glob.glob(os.path.join(bag_dir, "*.bag")))
    print(f"Auditing {len(bags)} bags...", file=sys.stderr)

    sections = ["# Cross-bag audit\n",
                f"Bags scanned: {len(bags)}",
                f"Bag dir: `{bag_dir}`",
                ""]
    for i, b in enumerate(bags):
        print(f"[{i+1}/{len(bags)}] {os.path.basename(b)}", file=sys.stderr)
        sections.append(fmt_bag_section(b))

    print("\n".join(sections))


if __name__ == "__main__":
    main()
