import { Component, type ErrorInfo, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

type Props = {
  children: ReactNode;
};

type State = {
  hasError: boolean;
};

type BoundaryProps = Props & {
  errorCopy: {
    eyebrow: string;
    title: string;
    body: string;
    reload: string;
  };
};

class AppErrorBoundaryInner extends Component<BoundaryProps, State> {
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
            <p className="eyebrow">{this.props.errorCopy.eyebrow}</p>
            <h1>{this.props.errorCopy.title}</h1>
            <p className="muted">{this.props.errorCopy.body}</p>
            <button className="primary-button" type="button" onClick={() => window.location.reload()}>
              {this.props.errorCopy.reload}
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}

export function AppErrorBoundary({ children }: Props) {
  const { t } = useTranslation();
  return (
    <AppErrorBoundaryInner
      errorCopy={{
        eyebrow: t("shell.runtime_error"),
        title: t("shell.runtime_error_title"),
        body: t("shell.runtime_error_body"),
        reload: t("shell.reload"),
      }}
    >
      {children}
    </AppErrorBoundaryInner>
  );
}
