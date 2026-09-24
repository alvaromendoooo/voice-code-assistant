/**
 * Applies an accepted edit via the IDE's own edit APIs (e.g. VS Code's WorkspaceEdit).
 * This is the only place a file is ever written -- the server never writes to disk.
 */

export async function applyUnifiedDiff(filePath: string, unifiedDiff: string): Promise<void> {
  throw new Error("not implemented");
}
