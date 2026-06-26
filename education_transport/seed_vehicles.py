#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed vehicles + transport assignments for june_23_edu
Run:
  source .venv/bin/activate && python3 odoo-bin shell \
    -c odoo.conf -d june_23_edu --no-http \
    < /home/cybrosys/odoo19/june23_erp/education_transport/seed_vehicles.py \
    2>&1 | grep -v "^INFO\|^DEBUG\|^WARNING\|^2026"
"""
env = env  # noqa
import datetime
today = datetime.date.today()

# ── Prerequisites ──────────────────────────────────────────────────
routes   = env["edu.transport.route"].search([], order="id asc", limit=10)
employees= env["hr.employee"].search([], limit=10)
ay       = env["education.academic.year"].search([], limit=1)
enrollments = env["education.enrollment"].search([], limit=10)

print(f"Routes     : {len(routes)}")
print(f"Employees  : {len(employees)}")
print(f"Acad. Year : {ay.name}")
print(f"Enrollments: {len(enrollments)}")

VEHICLES = [
    ("KL 01 AB 1001", "Tata Starbus 40",    40, "good"),
    ("KL 02 CD 2002", "Ashok Leyland Bus",   52, "good"),
    ("KL 03 EF 3003", "Force Traveller",     17, "fair"),
    ("KL 04 GH 4004", "Toyota HiAce",        15, "good"),
    ("KL 05 IJ 5005", "Tata Winger",         13, "good"),
    ("KL 06 KL 6006", "Mahindra Tourister",  20, "fair"),
    ("KL 07 MN 7007", "Volvo 9400",          48, "good"),
    ("KL 08 OP 8008", "Eicher Starline",     42, "poor"),
    ("KL 09 QR 9009", "Tata LP 909",         35, "fair"),
    ("KL 10 ST 1010", "Swaraj Mazda",        28, "good"),
]

print("\n── Creating Vehicles ──────────────────────────────────")
vehicles = []
for i, (reg, make, cap, cond) in enumerate(VEHICLES):
    existing = env["edu.transport.vehicle"].search(
        [("registration_no", "=", reg)], limit=1
    )
    if existing:
        print(f"  ⏭  {reg} already exists")
        vehicles.append(existing)
        continue

    route  = routes[i % len(routes)] if routes else False
    driver = employees[i % len(employees)] if employees else False
    last_service = today - datetime.timedelta(days=30 * (i + 1))

    v = env["edu.transport.vehicle"].create({
        "registration_no":  reg,
        "make_model":       make,
        "capacity":         cap,
        "condition":        cond,
        "route_id":         route.id if route else False,
        "driver_id":        driver.id if driver else False,
        "last_service_date": last_service,
        "active":           True,
    })
    vehicles.append(v)
    driver_name = driver.name if driver else "—"
    print(f"  ✔  {reg:20s}  {make:25s}  Driver: {driver_name}")

env.cr.commit()
print(f"\n✅  {len(vehicles)} vehicles ready.")

# ── Transport Assignments ──────────────────────────────────────────
print("\n── Creating Assignments ───────────────────────────────")
created = skipped = 0
for i, enr in enumerate(enrollments):
    route = routes[i % len(routes)] if routes else False
    if not route:
        continue
    stop = env["edu.transport.stop"].search(
        [("route_id", "=", route.id)], order="sequence asc", limit=1
    )
    if not stop:
        print(f"  ⚠️  No stop for {route.name}")
        continue

    exists = env["edu.transport.assignment"].search([
        ("enrollment_id",    "=", enr.id),
        ("academic_year_id", "=", ay.id),
    ], limit=1)
    if exists:
        print(f"  ⏭  {enr.student_name} already assigned")
        skipped += 1
        continue

    env["edu.transport.assignment"].create({
        "enrollment_id":    enr.id,
        "route_id":         route.id,
        "stop_id":          stop.id,
        "academic_year_id": ay.id,
        "transport_fee":    1200.0 + i * 100,
        "state":            "active",
    })
    created += 1
    print(f"  ✔  {enr.student_name:30s} → {route.name} [{stop.name}]")

env.cr.commit()
print(f"\n✅  Assignments — Created: {created}  Skipped: {skipped}")

# ── Summary ────────────────────────────────────────────────────────
print("\n" + "═" * 55)
print(f"  Vehicles    : {env['edu.transport.vehicle'].search_count([])}")
print(f"  Routes      : {env['edu.transport.route'].search_count([])}")
print(f"  Stops       : {env['edu.transport.stop'].search_count([])}")
print(f"  Assignments : {env['edu.transport.assignment'].search_count([])}")
print("═" * 55)
print("🎉 Done!")
