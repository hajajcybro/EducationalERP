#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hostel Demo Data Seeder
=======================
Run via Odoo shell:
    python3 /home/cybrosys/odoo19/odoo-bin shell \
        -d <your_db> \
        --addons-path=/home/cybrosys/odoo19/addons,/home/cybrosys/odoo19/june23_erp \
        < /home/cybrosys/odoo19/june23_erp/education_hostel/seed_hostel_demo.py

Creates:
  - 10 edu.hostel.property
  - 10 edu.hostel.room    (1 per property)
  - 10 edu.hostel.allocation (1 per enrollment, linked to the rooms)
"""
import datetime

env = env  # noqa — provided by odoo-bin shell

# ──────────────────────────────────────────────────────────────────────────────
# 0.  Prerequisites — fetch existing faculty & enrollments
# ──────────────────────────────────────────────────────────────────────────────
faculties = env["education.faculty"].search([], limit=10)
if not faculties:
    print("❌  No education.faculty records found. Please seed faculty first.")
    raise SystemExit(1)

enrollments = env["education.enrollment"].search(
    [("state", "=", "enrolled")], limit=10
)
if not enrollments:
    # Fallback: any enrollment
    enrollments = env["education.enrollment"].search([], limit=10)
if not enrollments:
    print("❌  No education.enrollment records found. Please seed enrollments first.")
    raise SystemExit(1)

print(f"✅  Found {len(faculties)} faculty and {len(enrollments)} enrollments")

# ──────────────────────────────────────────────────────────────────────────────
# 1.  edu.hostel.property  (10 records)
# ──────────────────────────────────────────────────────────────────────────────
PROPERTY_DATA = [
    {"name": "Boys Hostel A",   "block": "Block A", "total_capacity": 50},
    {"name": "Boys Hostel B",   "block": "Block B", "total_capacity": 40},
    {"name": "Girls Hostel A",  "block": "Block C", "total_capacity": 60},
    {"name": "Girls Hostel B",  "block": "Block D", "total_capacity": 45},
    {"name": "International House", "block": "Block E", "total_capacity": 30},
    {"name": "Faculty Quarters",    "block": "Block F", "total_capacity": 20},
    {"name": "PG Hostel",       "block": "Block G", "total_capacity": 35},
    {"name": "Research Scholar Block", "block": "Block H", "total_capacity": 25},
    {"name": "Sports Hostel",   "block": "Block I", "total_capacity": 40},
    {"name": "Annex Block",     "block": "Block J", "total_capacity": 30},
]

print("\n📦  Creating hostel properties...")
properties = []
for i, data in enumerate(PROPERTY_DATA):
    # Assign a warden (cycle through available faculty)
    warden = faculties[i % len(faculties)]
    prop = env["edu.hostel.property"].create({
        **data,
        "warden_id": warden.id,
        "active": True,
    })
    properties.append(prop)
    print(f"   ✔  {prop.name}  (Warden: {warden.name})")

env.cr.commit()
print(f"✅  {len(properties)} hostel properties created.")

# ──────────────────────────────────────────────────────────────────────────────
# 2.  edu.hostel.room  (10 records — 1 per property)
# ──────────────────────────────────────────────────────────────────────────────
ROOM_DATA = [
    {"room_no": "101", "room_type": "single",    "capacity": 1,  "amenities": "AC, Wi-Fi, Attached Bathroom"},
    {"room_no": "201", "room_type": "double",    "capacity": 2,  "amenities": "Wi-Fi, Fan, Common Bathroom"},
    {"room_no": "301", "room_type": "single",    "capacity": 1,  "amenities": "AC, Wi-Fi, Wardrobe"},
    {"room_no": "401", "room_type": "double",    "capacity": 2,  "amenities": "Fan, Study Table, Wi-Fi"},
    {"room_no": "501", "room_type": "dormitory", "capacity": 6,  "amenities": "Bunk Beds, Locker, Fan"},
    {"room_no": "601", "room_type": "single",    "capacity": 1,  "amenities": "AC, Attached Bathroom, TV"},
    {"room_no": "701", "room_type": "double",    "capacity": 2,  "amenities": "AC, Wi-Fi, Wardrobe"},
    {"room_no": "801", "room_type": "dormitory", "capacity": 4,  "amenities": "Fan, Bunk Beds, Wi-Fi"},
    {"room_no": "901", "room_type": "single",    "capacity": 1,  "amenities": "AC, Gym Access, Wi-Fi"},
    {"room_no": "A01", "room_type": "double",    "capacity": 2,  "amenities": "Fan, Study Table, Common Bathroom"},
]

print("\n🛏  Creating hostel rooms...")
rooms = []
for i, (prop, data) in enumerate(zip(properties, ROOM_DATA)):
    room = env["edu.hostel.room"].create({
        **data,
        "property_id": prop.id,
        "state": "available",
        "active": True,
    })
    rooms.append(room)
    print(f"   ✔  Room {room.room_no} in {prop.name}  [{data['room_type']}]")

env.cr.commit()
print(f"✅  {len(rooms)} hostel rooms created.")

# ──────────────────────────────────────────────────────────────────────────────
# 3.  edu.hostel.allocation  (10 records — 1 per enrollment)
# ──────────────────────────────────────────────────────────────────────────────
print("\n📋  Creating hostel allocations...")
today = datetime.date.today()
allocations = []

for i in range(min(10, len(enrollments), len(rooms))):
    enrollment = enrollments[i]
    room = rooms[i]
    date_from = today - datetime.timedelta(days=30 - i * 2)
    date_to   = today + datetime.timedelta(days=300)

    alloc = env["edu.hostel.allocation"].create({
        "enrollment_id": enrollment.id,
        "room_id":       room.id,
        "date_from":     date_from,
        "date_to":       date_to,
        "hostel_fee":    3500.0 + (i * 250),
        "state":         "draft",
        "notes":         f"Demo allocation #{i + 1} — auto-seeded.",
    })
    allocations.append(alloc)
    print(f"   ✔  Allocation {alloc.id}: {enrollment.display_name} → Room {room.room_no} ({room.property_id.name})")

env.cr.commit()
print(f"✅  {len(allocations)} allocations created (all in Draft).")

# ──────────────────────────────────────────────────────────────────────────────
# 4.  Confirm first 5 allocations to test the workflow
# ──────────────────────────────────────────────────────────────────────────────
print("\n🔄  Confirming first 5 allocations...")
for alloc in allocations[:5]:
    alloc.action_confirm()
    print(f"   ✔  Confirmed: {alloc.display_name}  — Room state: {alloc.room_id.state}")

env.cr.commit()
print("✅  5 allocations confirmed.")

# ──────────────────────────────────────────────────────────────────────────────
# 5.  Summary
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("HOSTEL SEED DATA SUMMARY")
print("=" * 60)
for prop in properties:
    prop.invalidate_recordset()   # refresh computed fields
    print(
        f"  {prop.name:35s}  Rooms: {prop.room_count}  "
        f"Occupied: {prop.occupied_count}  Warden: {prop.warden_id.name or '—'}"
    )
print("=" * 60)
print("🎉  Hostel demo data seeding complete!")
