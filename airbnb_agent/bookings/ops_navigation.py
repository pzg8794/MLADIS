from copy import deepcopy


OPS_NAV_ITEMS = [
    {
        "group": "Overview",
        "label": "Command Center",
        "href": "/ops/dashboard/",
        "icon": "dashboard",
        "description": "Command overview and live metrics",
        "tone": "#2563eb",
        "bg": "#dbeafe",
        "shortcut_action": "Open",
        "shortcut_tone": "blue",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="14" rx="1"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Reservations",
        "href": "/ops/reservations/",
        "icon": "reservations",
        "description": "Guest stays, channels, arrivals",
        "tone": "#0ea5e9",
        "bg": "#e0f2fe",
        "shortcut_action": "Manage",
        "shortcut_tone": "teal",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Calendar",
        "href": "/ops/calendar/",
        "icon": "calendar",
        "description": "Availability, blocks, pricing",
        "tone": "#7c3aed",
        "bg": "#ede9fe",
        "shortcut_action": "Open",
        "shortcut_tone": "teal",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Guests",
        "href": "/ops/customers/",
        "icon": "customers",
        "description": "Guest stays, channels, arrivals",
        "tone": "#0f766e",
        "bg": "#ccfbf1",
        "shortcut_action": "Manage",
        "shortcut_tone": "blue",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Maintenance",
        "href": "/ops/maintenance/",
        "icon": "maintenance",
        "description": "Issues, photos, repair status",
        "tone": "#f97316",
        "bg": "#ffedd5",
        "shortcut_action": "View",
        "shortcut_tone": "amber",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Payments",
        "href": "/ops/payments/",
        "icon": "payments",
        "description": "Checkout status and providers",
        "tone": "#0891b2",
        "bg": "#cffafe",
        "shortcut_action": "Open",
        "shortcut_tone": "blue",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Deposits",
        "href": "/ops/deposits/",
        "icon": "deposits",
        "description": "Holds, captures, releases",
        "tone": "#e11d48",
        "bg": "#ffe4e6",
        "shortcut_action": "Open",
        "shortcut_tone": "teal",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7H14.5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    },
    {
        "group": "Operations",
        "label": "Reports",
        "href": "/ops/reports/",
        "icon": "reports",
        "description": "Revenue, occupancy, trends",
        "tone": "#6d28d9",
        "bg": "#f3e8ff",
        "shortcut_action": "View",
        "shortcut_tone": "violet",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>',
    },
    {
        "group": "Operations",
        "label": "FairAgent",
        "href": "/ops/agent/",
        "icon": "fairagent",
        "description": "AI suggestions and training",
        "tone": "#0d9488",
        "bg": "#ccfbf1",
        "shortcut_action": "Manage",
        "shortcut_tone": "rose",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>',
    },
    {
        "group": "Business",
        "label": "Properties",
        "href": "/ops/properties/",
        "icon": "stays",
        "description": "Properties and availability",
        "tone": "#059669",
        "bg": "#d1fae5",
        "shortcut_action": "Manage",
        "shortcut_tone": "blue",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg>',
    },
    {
        "group": "Admin",
        "label": "Settings",
        "href": "/ops/settings/",
        "icon": "settings",
        "description": "Public site copy and identity",
        "tone": "#475569",
        "bg": "#e2e8f0",
        "shortcut_action": "Manage",
        "shortcut_tone": "amber",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    },
    {
        "group": "Admin",
        "label": "Admin",
        "href": "/ops/admin/",
        "icon": "users-admin",
        "description": "Access, roles, operators",
        "tone": "#1d4ed8",
        "bg": "#dbeafe",
        "shortcut_action": "Manage",
        "shortcut_tone": "violet",
        "icon_svg": '<svg class="modern-admin-rail-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="15" r="3"/><circle cx="9" cy="7" r="4"/><path d="M10 15H6a4 4 0 0 0-4 4v2"/><path d="m21.7 16.4-.9-.3"/><path d="m15.2 13.9-.9-.3"/><path d="m16.6 18.7.3-.9"/><path d="m19.1 12.2.3-.9"/></svg>',
    },
]


def ops_nav_public_items():
    return [
        {
            "group": item["group"],
            "label": item["label"],
            "href": item["href"],
            "icon": item["icon"],
            "description": item["description"],
            "tone": item["tone"],
            "bg": item["bg"],
            "shortcutAction": item["shortcut_action"],
            "shortcutTone": item["shortcut_tone"],
            **({"badge": item["badge"]} if item.get("badge") else {}),
        }
        for item in OPS_NAV_ITEMS
    ]


OPS_NAV_PUBLIC_ITEMS = ops_nav_public_items()


def _is_active(path, href):
    if href == "/ops/dashboard/":
        return path.rstrip("/") == "/ops/dashboard"
    normalized = href.rstrip("/")
    return path.rstrip("/") == normalized or path.startswith(f"{normalized}/")


def ops_nav_items_for_path(path):
    nav_items = deepcopy(OPS_NAV_ITEMS)
    for item in nav_items:
        item["is_active"] = _is_active(path, item["href"])
    return nav_items
