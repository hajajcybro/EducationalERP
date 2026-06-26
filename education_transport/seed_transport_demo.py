#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Education Transport — Demo Data Seeder
======================================
Run via Odoo shell:

    python3 /home/cybrosys/odoo19/odoo-bin shell \
        -d <your_db> \
        --addons-path=/home/cybrosys/odoo19/addons,/home/cybrosys/odoo19/june23_erp \
        < /home/cybrosys/odoo19/june23_erp/education_transport/seed_transport_demo.py

Creates:
    10  edu.transport.route      (each with 3–5 stops)
    10  edu.transport.vehicle    (one per route, linked to hr.employee driver)
    10  edu.transport.assignment (one per enrollment, one per academic year)
"""
import datetime

env = env  # noqa — provided by odoo-bin shell

SEP = "─" * 60

# ══════════════════════════════════════════════════════════════════
# 0.  Check prerequisites
# ══════════════════════════════════════════════════════════════════
academic_year = env["education.academic.year"].search([], limit=1)
if not academic_year:
    print("❌  No education.academic.year found. Please seed academic years first.")
    raise SystemExit(1)

enrollments = env["education.enrollment"].search([], limit=10)
if not enrollments:
    print("❌  No education.enrollment records found. Please seed enrollments first.")
    raise SystemExit(1)

employees = env["hr.employee"].search([], limit=10)
if not employees:
    print("⚠️   No hr.employee records found. Vehicles will have no driver.")

print(f"✅  Academic year  : {academic_year.name}")
print(f"✅  Enrollments    : {len(enrollments)}")
print(f"✅  Employees      : {len(employees)}")

# ══════════════════════════════════════════════════════════════════
# 1.  edu.transport.route  +  edu.transport.stop
# ══════════════════════════════════════════════════════════════════
ROUTES = [
    {
        "name": "Route 01 — North Campus",
        "description": "Covers northern residential areas",
        "stops": [
            {"name": "Main Gate",        "seq": 10, "pickup": 7.0,  "drop": 16.0, "km": 0.0},
            {"name": "Clock Tower",      "seq": 20, "pickup": 7.15, "drop": 15.75,"km": 2.5},
            {"name": "City Park",        "seq": 30, "pickup": 7.3,  "drop": 15.5, "km": 5.0},
            {"name": "North Junction",   "seq": 40, "pickup": 7.5,  "drop": 15.25,"km": 8.0},
        ],
    },
    {
        "name": "Route 02 — South Campus",
        "description": "Covers southern suburb areas",
        "stops": [
            {"name": "South Gate",       "seq": 10, "pickup": 7.0,  "drop": 16.0, "km": 0.0},
            {"name": "Market Square",    "seq": 20, "pickup": 7.2,  "drop": 15.8, "km": 3.0},
            {"name": "River Bridge",     "seq": 30, "pickup": 7.4,  "drop": 15.6, "km": 6.5},
        ],
    },
    {
        "name": "Route 03 — East Corridor",
        "description": "Covers eastern tech park area",
        "stops": [
            {"name": "Tech Park Gate",   "seq": 10, "pickup": 7.0,  "drop": 16.0, "km": 0.0},
            {"name": "Metro Station",    "seq": 20, "pickup": 7.25, "drop": 15.75,"km": 4.0},
            {"name": "Old Town",         "seq": 30, "pickup": 7.45, "drop": 15.55,"km": 7.0},
            {"name": "East Colony",      "seq": 40, "pickup": 7.6,  "drop": 15.4, "km": 10.0},
        ],
    },
    {
        "name": "Route 04 — West Hills",
        "description": "Covers western hill residential zone",
        "stops": [
            {"name": "West Gate",        "seq": 10, "pickup": 6.75, "drop": 16.25,"km": 0.0},
            {"name": "Hill View",        "seq": 20, "pickup": 7.0,  "drop": 16.0, "km": 5.0},
            {"name": "Valley Road",      "seq": 30, "pickup": 7.25, "drop": 15.75,"km": 9.0},
        ],
    },
    {
        "name": "Route 05 — Downtown Express",
        "description": "Express service to downtown area",
        "stops": [
            {"name": "Central Bus Stand","seq": 10, "pickup": 7.5,  "drop": 16.5, "km": 0.0},
            {"name": "High Street",      "seq": 20, "pickup": 7.65, "drop": 16.35,"km": 2.0},
            {"name": "Court Road",       "seq": 30, "pickup": 7.75, "drop": 16.25,"km": 3.5},
        ],
    },
    {
        "name": "Route 06 — Industrial Zone",
        "description": "Covers industrial area staff quarters",
        "stops": [
            {"name": "Factory Gate A",   "seq": 10, "pickup": 6.5,  "drop": 16.5, "km": 0.0},
            {"name": "Workers Colony",   "seq": 20, "pickup": 6.75, "drop": 16.25,"km": 4.0},
            {"name": "Sector 12",        "seq": 30, "pickup": 7.0,  "drop": 16.0, "km": 7.5},
            {"name": "Sector 15",        "seq": 40, "pickup": 7.2,  "drop": 15.8, "km": 11.0},
        ],
    },
    {
        "name": "Route 07 — University Road",
        "description": "Connects university area hostels",
        "stops": [
            {"name": "University Main",  "seq": 10, "pickup": 7.0,  "drop": 16.0, "km": 0.0},
            {"name": "PG Block",         "seq": 20, "pickup": 7.1,  "drop": 15.9, "km": 1.5},
            {"name": "Library Junction", "seq": 30, "pickup": 7.25, "drop": 15.75,"km": 3.0},
        ],
    },
    {
        "name": "Route 08 — Airport Road",
        "description": "Airport road residential corridor",
        "stops": [
            {"name": "Airport Entrance", "seq": 10, "pickup": 6.5,  "drop": 17.0, "km": 0.0},
            {"name": "Hotel Zone",       "seq": 20, "pickup": 6.75, "drop": 16.75,"km": 6.0},
            {"name": "Departure Plaza",  "seq": 30, "pickup": 7.0,  "drop": 16.5, "km": 10.0},
            {"name": "Cargo Terminal",   "seq": 40, "pickup": 7.2,  "drop": 16.3, "km": 13.0},
        ],
    },
    {
        "name": "Route 09 — Lake View",
        "description": "Scenic lake-side route",
        "stops": [
            {"name": "Lake Gate",        "seq": 10, "pickup": 7.0,  "drop": 16.0, "km": 0.0},
            {"name": "Boat Club Road",   "seq": 20, "pickup": 7.15, "drop": 15.85,"km": 3.0},
            {"name": "Fishing Village",  "seq": 30, "pickup": 7.3,  "drop": 15.7, "km": 5.5},
        ],
    },
    {
        "name": "Route 10 — Satellite Town",
        "description": "Satellite township connector",
        "stops": [
            {"name": "Satellite Gate",   "seq": 10, "pickup": 6.75, "drop": 16.25,"km": 0.0},
            {"name": "Township Centre",  "seq": 20, "pickup": 7.0,  "drop": 16.0, "km": 4.0},
            {"name": "Phase 2 Entry",    "seq": 30, "pickup": 7.2,  "drop": 15.8, "km": 7.0},
            {"name": "Phase 3 Entry",    "seq": 40, "pickup": 7.35, "drop": 15.65,"km": 9.5},
        ],
    },
]

print(f"\n{SEP}")
print("1. CREATING ROUTES + STOPS")
print(SEP)

routes = []
all_stops = []  # list of (route, stop) tuples

for rdata in ROUTES:
    route = env["edu.transport.route"].create({
        "name": rdata["name"],
        "description": rdata["description"],
        "active": True,
    })
    routes.append(route)

    stops = []
    for sdata in rdata["stops"]:
        stop = env["edu.transport.stop"].create({
            "route_id": route.id,
            "name": sdata["name"],
            "sequence": sdata["seq"],
            "pickup_time": sdata["pickup"],
            "drop_time": sdata["drop"],
            "distance_km": sdata["km"],
        })
        stops.append(stop)
        all_stops.append((route, stop))

    print(f"   ✔  {route.name}  ({len(stops)} stops)")

env.cr.commit()
print(f"✅  {len(routes)} routes created with stops.")

# ══════════════════════════════════════════════════════════════════
# 2.  fleet.vehicle  (10 school vehicles — one per route)
# ══════════════════════════════════════════════════════════════════
VEHICLES = [
    {"reg": "KL 01 AB 1001", "make": "Tata Starbus 40",  "cap": 40, "cond": "good"},
    {"reg": "KL 02 CD 2002", "make": "Ashok Leyland Bus","cap": 52, "cond": "good"},
    {"reg": "KL 03 EF 3003", "make": "Force Traveller",  "cap": 17, "cond": "fair"},
    {"reg": "KL 04 GH 4004", "make": "Toyota HiAce",     "cap": 15, "cond": "good"},
    {"reg": "KL 05 IJ 5005", "make": "Tata Winger",      "cap": 13, "cond": "good"},
    {"reg": "KL 06 KL 6006", "make": "Mahindra Tourister","cap": 20,"cond": "fair"},
    {"reg": "KL 07 MN 7007", "make": "Volvo 9400",       "cap": 48, "cond": "good"},
    {"reg": "KL 08 OP 8008", "make": "Eicher Starline",  "cap": 42, "cond": "poor"},
    {"reg": "KL 09 QR 9009", "make": "Tata LP 909",      "cap": 35, "cond": "fair"},
    {"reg": "KL 10 ST 1010", "make": "Swaraj Mazda",     "cap": 28, "cond": "good"},
]

import datetime as dt
today = dt.date.today()

print(f"\n{SEP}")
print("2. CREATING VEHICLES")
print(SEP)

vehicles = []
for i, (vdata, route) in enumerate(zip(VEHICLES, routes)):
    driver = employees[i % len(employees)] if employees else False
    last_service = today - dt.timedelta(days=30 * (i + 1))

    vehicle = env["edu.transport.vehicle"].create({
        "registration_no": vdata["reg"],
        "make_model":      vdata["make"],
        "capacity":        vdata["cap"],
        "condition":       vdata["cond"],
        "driver_id":       driver.id if driver else False,
        "route_id":        route.id,
        "last_service_date": last_service,
        "active":          True,
    })
    vehicles.append(vehicle)
    driver_name = driver.name if driver else "—"
    print(f"   ✔  {vehicle.registration_no:20s}  {vdata['make']:25s}  Driver: {driver_name}")

env.cr.commit()
print(f"✅  {len(vehicles)} vehicles created.")

# ══════════════════════════════════════════════════════════════════
# 3.  edu.transport.assignment  (one per enrollment)
# ══════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("3. CREATING STUDENT TRANSPORT ASSIGNMENTS")
print(SEP)

assignments = []
fees = [1200.0, 1500.0, 1800.0, 2000.0, 1100.0,
        1350.0, 1600.0, 1750.0, 2100.0, 1450.0]

for i in range(min(10, len(enrollments))):
    enrollment = enrollments[i]
    # pick route + its first stop
    route = routes[i % len(routes)]
    # get first stop of this route
    stop = env["edu.transport.stop"].search(
        [("route_id", "=", route.id)], order="sequence asc", limit=1
    )
    if not stop:
        print(f"   ⚠️  No stop found for {route.name}, skipping.")
        continue

    assignment = env["edu.transport.assignment"].create({
        "enrollment_id":   enrollment.id,
        "route_id":        route.id,
        "stop_id":         stop.id,
        "academic_year_id": academic_year.id,
        "transport_fee":   fees[i],
        "state":           "active",
    })
    assignments.append(assignment)
    print(
        f"   ✔  {assignment.student_name or enrollment.display_name:30s}"
        f"  →  {route.name:30s}  [{stop.name}]  Fee: {fees[i]}"
    )

env.cr.commit()
print(f"✅  {len(assignments)} transport assignments created.")

# ══════════════════════════════════════════════════════════════════
# 4.  Verification summary
# ══════════════════════════════════════════════════════════════════
print(f"\n{'═' * 60}")
print("TRANSPORT MODULE — DATA VERIFICATION SUMMARY")
print('═' * 60)

total_routes   = env["edu.transport.route"].search_count([])
total_stops    = env["edu.transport.stop"].search_count([])
total_vehicles = env["edu.transport.vehicle"].search_count([])
total_assigns  = env["edu.transport.assignment"].search_count([])

print(f"  edu.transport.route      : {total_routes}")
print(f"  edu.transport.stop       : {total_stops}")
print(f"  edu.transport.vehicle    : {total_vehicles}")
print(f"  edu.transport.assignment : {total_assigns}")
print()

# Route-wise vehicle + stop count
for route in routes:
    route.invalidate_recordset()
    print(
        f"  {route.name:40s}  "
        f"Stops: {route.stop_count:2d}  "
        f"Vehicles: {len(route.vehicle_ids)}"
    )

print('═' * 60)
print("🎉  Transport demo data seeding complete!")
