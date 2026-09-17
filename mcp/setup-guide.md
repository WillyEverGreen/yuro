# MCP Configuration & Synchronization Guide

Kortex uses a hybrid architecture:
1. **CLI Path (`cbm`)**: The primary execution path for code graph queries (`cbm arch`, `cbm trace`, `cbm search`). Zero JSON schema prompt tax.
2. **MCP Path (`codebase-memory`)**: Configured in `~/.gemini/config/mcp_config.json` as lazy tools.

## Setting up on a New Machine:

### Windows:
Place `codebase-memory-mcp.exe` in `C:\tools\`.
Copy `mcp_config.global.json` to:
`%USERPROFILE%\.gemini\config\mcp_config.json`

### macOS / Linux:
Place `codebase-memory-mcp` in `/usr/local/bin/` (or `~/.local/bin/`).
Make it executable: `chmod +x /usr/local/bin/codebase-memory-mcp`
Configure in `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "codebase-memory": {
      "command": "/usr/local/bin/codebase-memory-mcp",
      "args": []
    }
  }
}
```
