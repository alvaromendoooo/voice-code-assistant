/**
 * Renders a proposed unified diff using the host IDE's native diff view, and reports
 * the user's accept/reject decision back to the caller.
 */

export type DiffDecisionResult = "accepted" | "rejected";

export async function showDiff(
  filePath: string,
  unifiedDiff: string,
  rationale: string
): Promise<DiffDecisionResult> {
  throw new Error("not implemented");
}
