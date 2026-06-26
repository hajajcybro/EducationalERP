#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed ONLY the transport assignments (routes+vehicles already exist).
Run via:
    source .venv/bin/activate && python3 odoo-bin shell \
      -c odoo.conf -d june_22_education --no-http \
      < /home/cybrosys/odoo19/june23_erp/education_transport/seed_assignments_only.py 2>&1 | grep -v "^INFO\|^DEBUG\|^WARNING"
"""
env = env  # noqa

academic_year = env["education.academic.year"].search([], limit=1)
enrollments   = env["education.enrollment"].search([], limit=10)
routes        = env["edu.transport.route"].search([], order="id asc", limit=10)

print(f"Academic year : {academic_year.name}")
print(f"Enrollments   : {len(enrollments)}")
print(f"Routes        : {len(routes)}")

fees = [1200.0, 1500.0, 1800.0, 2000.0, 1100.0,
        1350.0, 1600.0, 1750.0, 2100.0, 1450.0]

created = 0
skipped = 0

for i in range(min(10, len(enrollments), len(routes))):
    enrollment = enrollments[i]
    route      = routes[i]

    # Skip if already exists
    existing = env["edu.transport.assignment"].search([
        ("enrollment_id",    "=", enrollment.id),
        ("academic_year_id", "=", academic_year.id),
    ], limit=1)
    if existing:
        print(f"   ⏭  SKIP  {enrollment.display_name}  (already assigned)")
        skipped += 1
        continue

    stop = env["edu.transport.stop"].search(
        [("route_id", "=", route.id)], order="sequence asc", limit=1
    )
    if not stop:
        print(f"   ⚠️  No stop for {route.name}")
        continue

    assignment = env["edu.transport.assignment"].create({
        "enrollment_id":    enrollment.id,
        "route_id":         route.id,
        "stop_id":          stop.id,
        "academic_year_id": academic_year.id,
        "transport_fee":    fees[i],
        "state":            "active",
    })
    created += 1
    print(f"   ✔  {assignment.student_name or enrollment.display_name:30s}  →  {route.name}  [{stop.name}]")

env.cr.commit()
print(f"\n✅  Created: {created}  |  Skipped (existing): {skipped}")

# ── Final summary ──
print("\n" + "═" * 60)
print(f"  Routes      : {env['edu.transport.route'].search_count([])}")
print(f"  Stops       : {env['edu.transport.stop'].search_count([])}")
print(f"  Vehicles    : {env['edu.transport.vehicle'].search_count([])}")
print(f"  Assignments : {env['edu.transport.assignment'].search_count([])}")
print("═" * 60)
print("🎉  Done!")
