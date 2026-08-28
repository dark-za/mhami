import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
};

type State = {
  hasError: boolean;
};

export class AppErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("App shell error", error, info);
  }

  override render() {
    if (this.state.hasError) {
      return (
        <main className="app-shell">
          <section className="panel">
            <p className="eyebrow">Runtime error</p>
            <h1>Something went wrong</h1>
            <p className="muted">The shell hit an unexpected client-side error. Reload the page to continue.</p>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
