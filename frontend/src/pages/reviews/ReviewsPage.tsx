// Re-export of the canonical ReviewsPage so route lazy imports target a
// dedicated file. The actual implementation lives in `pages/shared` to keep
// the existing module graph intact while we migrate the folder layout.
export { ReviewsPage } from "../shared/ReviewsPage";
export { ReviewsPage as default } from "../shared/ReviewsPage";
