// Re-export of the canonical ExportsPage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { ExportsPage } from "../shared/ExportsPage";
export { ExportsPage as default } from "../shared/ExportsPage";
