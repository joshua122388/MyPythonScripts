# sddc_token.py

A Linux tool for updating the Broadcom download token in VMware Cloud Foundation (VCF) depot configuration files. Supports both SDDC Manager and the Async Patch Tool via an interactive menu.

## Requirements

- Python 3.6+
- Linux — must run on a VCF SDDC Manager appliance
- Root or sudo privileges (writes to system config paths and restarts `lcm` via `systemctl`)

No third-party packages required — standard library only.

## Usage

```bash
sudo python3 sddc_token.py
```

The script prompts for your Broadcom download token on startup, then presents the main menu.

## Menu Options

```
+------------------------------------------------------------+
|                        Main Menu                           |
+------------------------------------------------------------+
| 1 | SDDC Manager Depot (online method only)                |
| 2 | Async Patch Tool (online method only)                  |
+------------------------------------------------------------+
```

### Option 1 — SDDC Manager Depot
Updates the following properties in:
```
/opt/vmware/vcf/lcm/lcm-app/conf/application-prod.properties
```

| Property | Value set |
|---|---|
| `lcm.depot.adapter.host` | `dl.broadcom.com` |
| `lcm.depot.adapter.remote.rootDir` | `/<token>/PROD` |
| `lcm.depot.adapter.remote.repoDir` | `/COMP/SDDC_MANAGER_VCF` |
| `lcm.depot.adapter.remote.lcmManifestDir` | `/COMP/SDDC_MANAGER_VCF/lcm/manifest` |
| `lcm.depot.adapter.remote.lcmProductVersionCatalogDir` | `/COMP/SDDC_MANAGER_VCF/lcm/productVersionCatalog` |

After writing the file, restarts the `lcm` service:
```bash
systemctl restart lcm
```

### Option 2 — Async Patch Tool
Updates the same set of properties in:
```
/home/vcf/asyncPatchTool/conf/application-asyncpatch.properties
```

If the file does not exist, the operation is skipped with a warning. After writing, restarts the `lcm` service.

## How It Works

For each target property, the script:
1. Searches for an existing `key=...` line using a regex match
2. If found — replaces the line in place
3. If not found — appends the new `key=value` line at the end of the file

This means the script is safe to run multiple times; it will update existing values rather than duplicate them.

## Notes

- The download token is used to build the `rootDir` path in the format `/<token>/PROD`
- Both options only support the **online depot method** — offline methods are not handled by this script
- The script must be run directly on the SDDC Manager appliance where the config files reside
