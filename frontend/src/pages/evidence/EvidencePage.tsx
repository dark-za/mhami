// Re-export of the canonical EvidencePage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { EvidencePage } from "../shared/EvidencePage";
export { EvidencePage as default } from "../shared/EvidencePage";
