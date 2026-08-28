// Re-export of the canonical PilotPage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { PilotPage } from "../shared/PilotPage";
export { PilotPage as default } from "../shared/PilotPage";
