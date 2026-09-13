"""A small, self-drawn line-icon set used across the dashboard.

Every icon is plain inline SVG (24x24 viewBox, currentColor stroke) so it
recolors with CSS like text does, needs no external icon font or CDN, and
looks the same on every machine. `icon(name, size)` is registered as a
Jinja global in webapp/app.py, so templates just call `{{ icon('home') }}`.
"""
from markupsafe import Markup

# Each entry is the *inner* SVG markup only (no outer <svg> tag). Everything
# uses stroke="currentColor" / fill="none" by default (set on the wrapper);
# a handful of small accent dots/stars set their own fill for a solid mark.
ICONS = {
    "home": '<path d="M4 11.5 12 4l8 7.5"/><path d="M6 10v8.5a1 1 0 0 0 1 1h3.2V14h3.6v5.5H17a1 1 0 0 0 1-1V10"/>',
    "book-open": '<path d="M12 6.2C10.6 5 8.6 4.3 5.8 4.3c-.6 0-1 .5-1 1v12c0 .5.4 1 1 1 2.8 0 4.8.7 6.2 2 1.4-1.3 3.4-2 6.2-2 .6 0 1-.5 1-1v-12c0-.5-.4-1-1-1-2.8 0-4.8.7-6.2 1.9Z"/><path d="M12 6.2v13"/>',
    "sparkle": '<path d="M12 3.5c.4 3 1.6 4.6 4.6 5-3 .4-4.2 1.6-4.6 4.6-.4-3-1.6-4.2-4.6-4.6 3-.4 4.2-2 4.6-5Z"/><path d="M18.5 14c.2 1.6.9 2.4 2.5 2.6-1.6.2-2.3.9-2.5 2.5-.2-1.6-.9-2.3-2.5-2.5 1.6-.2 2.3-1 2.5-2.6Z"/>',
    "compass": '<circle cx="12" cy="12" r="8.3"/><path d="m14.6 9.4-1.3 3.9-3.9 1.3 1.3-3.9z"/>',
    "folder": '<path d="M3.5 6.7c0-.7.6-1.2 1.2-1.2h3.6l1.8 2h9.2c.7 0 1.2.6 1.2 1.2V17c0 .7-.6 1.3-1.3 1.3H4.8c-.7 0-1.3-.6-1.3-1.3Z"/>',
    "scale": '<path d="M12 3.3v16.4M8.7 20h6.6M4.3 8.4h4.4M15.3 8.4h4.4M4.3 8.4 2.2 13a2.6 2.6 0 0 0 5 0zM19.7 8.4l-2.1 4.6a2.6 2.6 0 0 0 5 0z"/>',
    "target": '<circle cx="12" cy="12" r="8.3"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/>',
    "trending-up": '<path d="m3.5 16 5.6-5.8 3.8 3.6L20.5 6"/><path d="M15.2 6h5.3v5.3"/>',
    "sliders": '<path d="M4 6.5h7.5M15.5 6.5H20M4 12h3.5M11.5 12H20M4 17.5h10.5M18.5 17.5H20"/><circle cx="13.5" cy="6.5" r="2"/><circle cx="9.5" cy="12" r="2"/><circle cx="16.5" cy="17.5" r="2"/>',
    "search": '<circle cx="10.8" cy="10.8" r="6.3"/><path d="m20 20-4.4-4.4"/>',
    "bell": '<path d="M6.2 16.2V11a5.8 5.8 0 0 1 11.6 0v5.2l1.7 2.1H4.5Z"/><path d="M9.6 20.3a2.4 2.4 0 0 0 4.8 0"/>',
    "menu": '<path d="M4 6.5h16M4 12h16M4 17.5h16"/>',
    "graduation-cap": '<path d="M12 4.3 2.5 9l9.5 4.7L21.5 9Z"/><path d="M6.2 11.7v4.6c0 1.4 2.6 2.9 5.8 2.9s5.8-1.5 5.8-2.9v-4.6"/><path d="M21.5 9v6"/>',
    "layers": '<path d="M12 3.7 3.2 8.3 12 13l8.8-4.7Z"/><path d="m3.2 13 8.8 4.7 8.8-4.7"/>',
    "grid": '<rect x="3.7" y="3.7" width="7" height="7" rx="1.2"/><rect x="13.3" y="3.7" width="7" height="7" rx="1.2"/><rect x="3.7" y="13.3" width="7" height="7" rx="1.2"/><rect x="13.3" y="13.3" width="7" height="7" rx="1.2"/>',
    "activity": '<path d="M3 12.5h4l2-6.4L13 19l2.3-6.5H21"/>',
    "check-circle": '<circle cx="12" cy="12" r="8.3"/><path d="m8 12.3 2.6 2.6 5.4-5.8"/>',
    "circle": '<circle cx="12" cy="12" r="7"/>',
    "clock": '<circle cx="12" cy="12" r="8.3"/><path d="M12 7.4V12l3.1 1.9"/>',
    "bookmark": '<path d="M6.7 4.2h10.6a1 1 0 0 1 1 1V19l-6.3-3.9-6.3 3.9V5.2a1 1 0 0 1 1-1Z"/>',
    "star": '<path d="M12 3.6l2.3 4.9 5.4.6-4 3.6 1.1 5.3L12 15.3l-4.8 2.7 1.1-5.3-4-3.6 5.4-.6Z" fill="currentColor" stroke="none"/>',
    "users": '<circle cx="9" cy="8.3" r="3"/><path d="M3.7 19c0-2.9 2.4-5 5.3-5s5.3 2.1 5.3 5"/><circle cx="16.7" cy="9" r="2.3"/><path d="M15.3 14.1c2.3.3 3.9 2 3.9 4.9"/>',
    "code": '<path d="m9 8-4.3 4L9 16M15 8l4.3 4L15 16"/>',
    "bar-chart": '<path d="M4 19V11M10 19V5M16 19v-7M21 19H3"/>',
    "cpu": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><rect x="10.2" y="10.2" width="3.6" height="3.6"/><path d="M12 3.3v3M12 17.7v3M3.3 12h3M17.7 12h3"/>',
    "cloud": '<path d="M7.2 18.3a3.9 3.9 0 0 1-.5-7.8 5.4 5.4 0 0 1 10.6-1.2A4.1 4.1 0 0 1 16.9 18.3Z"/>',
    "shield": '<path d="M12 3.6 5.3 6v5.4c0 4.4 2.9 7.3 6.7 8.7 3.8-1.4 6.7-4.3 6.7-8.7V6Z"/>',
    "smartphone": '<rect x="7.2" y="3" width="9.6" height="18" rx="2"/><path d="M11 18.2h2"/>',
    "palette": '<path d="M12 3.7a8.3 8.3 0 1 0 0 16.6c1 0 1.7-.8 1.7-1.7 0-.5-.2-.9-.5-1.2a1.5 1.5 0 0 1 1.1-2.6h1.8a3.7 3.7 0 0 0 3.6-3.7c0-4.1-3.5-7.4-7.7-7.4Z"/><circle cx="7.6" cy="11" r="1" fill="currentColor" stroke="none"/><circle cx="9.6" cy="7.6" r="1" fill="currentColor" stroke="none"/><circle cx="14.4" cy="7.2" r="1" fill="currentColor" stroke="none"/><circle cx="16.3" cy="10.6" r="1" fill="currentColor" stroke="none"/>',
    "briefcase": '<rect x="3.5" y="8" width="17" height="10.8" rx="1.5"/><path d="M8.5 8V6.2a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2V8"/><path d="M3.5 13h17"/>',
    "server": '<rect x="4" y="4.3" width="16" height="6" rx="1.3"/><rect x="4" y="13.7" width="16" height="6" rx="1.3"/><path d="M7.3 7.3h.01M7.3 16.7h.01"/>',
    "database": '<ellipse cx="12" cy="6" rx="7" ry="2.6"/><path d="M5 6v12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6V6"/><path d="M5 12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6"/>',
}


def icon_svg(name: str, size: int = 18, stroke: float = 1.8, cls: str = "") -> Markup:
    """Renders one icon as an inline <svg>. Unknown names fall back to a
    plain circle rather than raising, so a stray/typo'd icon key degrades
    gracefully instead of crashing a page."""
    inner = ICONS.get(name, ICONS["circle"])
    class_attr = f' class="{cls}"' if cls else ""
    return Markup(
        f'<svg{class_attr} width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{inner}</svg>'
    )


# Category -> icon name, shared by CAREER_ROLES (app.py) so a role's icon
# always matches its track's category icon everywhere in the app.
CATEGORY_ICON = {
    "Web Development": "code",
    "Data Science": "bar-chart",
    "Machine Learning & AI": "cpu",
    "Cloud Computing": "cloud",
    "Cybersecurity": "shield",
    "Mobile Development": "smartphone",
    "UI/UX Design": "palette",
    "Business & Product Management": "briefcase",
    "DevOps & SRE": "server",
    "Databases & Data Engineering": "database",
}
