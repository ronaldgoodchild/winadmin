# Roadmap / ideas

Comment on (or open) an issue first so we don't duplicate work.

## Good first issues
- [x] Add screenshots (use `localhost` - no real hostnames or IPs)
- [ ] Split the 3,000-line `main.py` into one module per category
- [ ] Add unit tests for `win_admin_tools.py` (parsers, formatters)
- [ ] Replace deprecated `wmi` / `wmic` calls with CIM cmdlets or `psutil`

## Security
- [ ] Encrypt saved remote credentials (Windows Credential Manager)
- [ ] Confirmation and audit trail for destructive actions (restart, shutdown, AD changes)

## Features
- [ ] Run a command or script on several computers at once
- [ ] Event Log viewer with filters
- [ ] Scheduled tasks, printers and shares management
- [ ] Export any table to CSV / HTML
