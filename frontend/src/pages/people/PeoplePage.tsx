// Re-export of the canonical PeoplePage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { PeoplePage } from "../shared/PeoplePage";
export { PeoplePage as default } from "../shared/PeoplePage";
