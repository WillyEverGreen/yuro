# TokenSaver v5 Limitations & Scope Boundaries

1. **Language Coverage Quality**:
   - `PRECISE`: Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, C# (via Tree-sitter AST).
   - `FALLBACK`: JSON, YAML, TOML, Markdown, and unsupported text formats (via conservative regex).

2. **Provider Telemetry**:
   - TokenSaver measures exact **ESTIMATED LOCAL CONTEXT TOKENS**. Provider-level tokens (Gemini / Claude / OpenAI API output telemetry) are tracked separately when available via Altimeter.
