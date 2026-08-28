// Re-export of the canonical AIControlPage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { AIControlPage } from "../shared/AIControlPage";
export { AIControlPage as default } from "../shared/AIControlPage";
