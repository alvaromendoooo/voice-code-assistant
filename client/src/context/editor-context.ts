/**
 * Snapshots the active editor state (file, selection, cursor) to attach to outgoing
 * voice.utterance messages. Phase 1 only -- no project-wide context yet.
 */

import type { EditorContext } from "../connection/messages";

export function captureEditorContext(): EditorContext {
  throw new Error("not implemented");
}
