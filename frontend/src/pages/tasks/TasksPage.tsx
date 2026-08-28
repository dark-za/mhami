// Re-export of the canonical TasksPage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { TasksPage } from "../shared/TasksPage";
export { TasksPage as default } from "../shared/TasksPage";
