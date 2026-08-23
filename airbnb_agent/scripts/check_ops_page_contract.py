#!/usr/bin/env python3
import hashlib
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

RETIRED_PATHS = (
    "airbnb_agent/bookings/templates/bookings/ops_dashboard.html",
    "airbnb_agent/bookings/templates/bookings/ops_calendar.html",
    "airbnb_agent/bookings/templates/bookings/ops_reports.html",
    "airbnb_agent/bookings/templates/bookings/ops_reservations.html",
    "airbnb_agent/bookings/templates/bookings/modern_ops_calendar.html",
    "airbnb_agent/bookings/static/frontend/modern-dashboard/assets/ops-calendar.css",
    "frontend/public/assets/ops-calendar.css",
    "frontend/src/application/PropertyListingsFactory.ts",
    "frontend/src/application/PropertyListingsService.ts",
    "frontend/src/domain/properties.ts",
    "frontend/src/infrastructure/PropertyListingsRepository.ts",
    "frontend/src/ui/pages/OpsAgentPage.tsx",
    "frontend/src/ui/pages/OpsMaintenancePage.tsx",
    "frontend/src/ui/pages/OpsStayPortfolioPage.tsx",
    "frontend/src/ui/pages/ops-stays-page.css",
)

REQUIRED_PATHS = (
    "airbnb_agent/bookings/templates/bookings/modern_dashboard.html",
    "airbnb_agent/bookings/templates/bookings/modern_ops_agent.html",
    "airbnb_agent/bookings/templates/bookings/modern_ops_customers.html",
    "airbnb_agent/bookings/templates/bookings/modern_ops_maintenance.html",
    "airbnb_agent/bookings/templates/bookings/modern_ops_stays.html",
    "airbnb_agent/bookings/static/frontend/modern-dashboard/assets/ops-agent.css",
    "airbnb_agent/bookings/static/frontend/modern-dashboard/assets/ops-maintenance.css",
    "frontend/public/assets/ops-agent.css",
    "frontend/public/assets/ops-maintenance.css",
    "frontend/src/ui/pages/DashboardPage.tsx",
    "frontend/src/ui/pages/OpsCalendarPage.tsx",
    "frontend/src/ui/pages/OpsDepositsPage.tsx",
    "frontend/src/ui/pages/OpsPaymentsPage.tsx",
    "frontend/src/ui/pages/OpsReportsPage.tsx",
    "frontend/src/ui/pages/OpsReservationsPage.tsx",
    "frontend/src/ui/pages/OpsSettingsPage.tsx",
)

APPROVED_DESIGN_MARKERS = {
    "airbnb_agent/bookings/templates/bookings/modern_ops_agent.html": (
        'class="ops-agent-page"',
        "Live Conversation Insights",
        "Protected Guardrails",
    ),
    "airbnb_agent/bookings/templates/bookings/modern_ops_maintenance.html": (
        'class="ops-mnt-page"',
        "Maintenance &amp; Work Orders",
        "Work Orders",
    ),
    "frontend/src/ui/pages/OpsReportsPage.tsx": (
        'className="dashboard-content ops-page ops-rpt"',
        "Reports &amp; Analytics",
        "function RevenueChart",
        "function ChannelsCard",
        "function DonutCard",
        "function HeatmapCard",
        "function StaysCard",
        "function InsightsCard",
        'className="ops-charts-row"',
        'className="ops-bottom-row"',
        'href="/api/ops/reports/"',
    ),
    "frontend/src/ui/pages/OpsSettingsPage.tsx": (
        'className="dashboard-content settings-v4-page"',
        "Authoritative controls",
        "SettingsSectionPanel",
    ),
}

FORBIDDEN_RUNTIME_MARKERS = {
    "airbnb_agent/bookings/templates/bookings/base_ops.html": (
        "Search reservations, guests, properties",
        "<span>8</span>",
    ),
    "airbnb_agent/bookings/templates/bookings/modern_ops_agent.html": (
        "Maria Rodriguez",
        "Auto-generated",
    ),
    "airbnb_agent/bookings/templates/bookings/modern_ops_maintenance.html": (
        "WO-2026-0104",
        "AI-Generated Bill / Report Preview",
    ),
    "frontend/src/ui/components/DashboardLayout.tsx": (
        "Piter Garcia",
        "Search reservations, guests, properties",
        "Notifications",
    ),
    "frontend/src/ui/pages/OpsSettingsPage.tsx": (
        "localStorage",
    ),
    "frontend/src/ui/pages/OpsReportsPage.tsx": (
        "RealDataChart",
        "ChartCard",
        "ops-rpt-real-grid",
        "ops-live-report-grid",
    ),
    "airbnb_agent/bookings/templates/registration/login.html": (
        "Welcome back, Piter",
        "$12,450",
        "3 Properties",
        "industry-leading encryption",
    ),
}

APPROVED_SOURCE_SHA256 = {
    "airbnb_agent/bookings/templates/bookings/modern_ops_agent.html": "0789e706b7de9168763a9df70a160db7436395933df3cecce60fd6be83d13704",
    "airbnb_agent/bookings/templates/bookings/modern_ops_maintenance.html": "0390b1866dfb0208bbcb25520dfca6984bb8c62f7e041ef881391d70ac8283af",
    "frontend/src/ui/pages/OpsReportsPage.tsx": "7c0c26eea502d1157668a7a5ebda0bde8ec647a5f089ea212b1a55a59930a2f1",
    "frontend/src/ui/pages/OpsSettingsPage.tsx": "59889a8308d864b25233e3ba53d8f0a114190c66b5e02622b77499a0312afb82",
    "frontend/src/ui/pages/opsreports.css": "e4ff18e984e44b7f7ebe6e15b92469b9f56d0df25670e32f09ba083bf2bbc55b",
}


def contract_path(relative_path: str) -> Path:
    app_prefix = "airbnb_agent/"
    if relative_path.startswith(app_prefix):
        return APP_ROOT / relative_path.removeprefix(app_prefix)
    return PROJECT_ROOT / relative_path


def main() -> int:
    problems = []
    frontend_available = (PROJECT_ROOT / "frontend/package.json").is_file()
    for relative_path in RETIRED_PATHS:
        if contract_path(relative_path).exists():
            problems.append(f"retired implementation exists: {relative_path}")

    for relative_path in REQUIRED_PATHS:
        if relative_path.startswith("frontend/") and not frontend_available:
            continue
        if not contract_path(relative_path).is_file():
            problems.append(f"canonical implementation is missing: {relative_path}")

    for relative_path, markers in APPROVED_DESIGN_MARKERS.items():
        approved_path = contract_path(relative_path)
        if not approved_path.is_file():
            continue
        source = approved_path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in source:
                problems.append(f"approved design marker is missing: {relative_path}: {marker}")

    for relative_path, markers in FORBIDDEN_RUNTIME_MARKERS.items():
        runtime_path = contract_path(relative_path)
        if not runtime_path.is_file():
            continue
        source = runtime_path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in source:
                problems.append(f"sample or unsupported runtime marker is present: {relative_path}: {marker}")

    for relative_path, expected_hash in APPROVED_SOURCE_SHA256.items():
        if relative_path.startswith("frontend/") and not frontend_available:
            continue
        approved_path = contract_path(relative_path)
        if not approved_path.is_file():
            continue
        actual_hash = hashlib.sha256(approved_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            problems.append(f"approved design fingerprint changed: {relative_path}")

    views_source = (APP_ROOT / "bookings/views.py").read_text(encoding="utf-8")
    reports_source = (APP_ROOT / "bookings/reports.py").read_text(encoding="utf-8")
    urls_source = (APP_ROOT / "bookings/urls.py").read_text(encoding="utf-8")
    if 'class ModernOpsAgentView(TemplateView):\n    template_name = "bookings/modern_ops_agent.html"' not in views_source:
        problems.append("FairAgent route is not locked to the approved template")
    if 'class ModernOpsMaintenanceView(TemplateView):\n    template_name = "bookings/modern_ops_maintenance.html"' not in views_source:
        problems.append("maintenance route is not locked to the approved template")
    if 'template_name = "bookings/modern_dashboard.html"' not in reports_source:
        problems.append("reports route is not using the canonical shell")
    if 'path("ops/settings/", ModernOpsDashboardView.as_view(), name="ops-settings")' not in urls_source:
        problems.append("settings route is not using the approved React shell")

    if problems:
        print("Operations page contract failed:")
        for problem in problems:
            print(f" - {problem}")
        return 1

    print("Operations page contract passed: approved designs are present and route-locked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
