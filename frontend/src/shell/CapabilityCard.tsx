/** Capability preflight: secure-context + camera check. */

import { useEffect, useState } from "react";

import { StateCard } from "./ui";

type CapabilityState = "checking" | "ready" | "limited";

export function CapabilityCard() {
  const [state, setState] = useState<CapabilityState>("checking");

  useEffect(() => {
    const hasCamera = Boolean(globalThis.navigator?.mediaDevices?.getUserMedia);
    const secure = Boolean(globalThis.isSecureContext);
    setState(hasCamera && secure ? "ready" : "limited");
  }, []);

  const copy =
    state === "checking"
      ? {
          title: "Checking browser capabilities",
          body: "The shell is evaluating secure camera support.",
          tone: "neutral",
        }
      : state === "ready"
      ? {
          title: "Chrome camera preflight ready",
          body: "The shell can request camera access only at the point of use.",
          tone: "success",
        }
      : {
          title: "Camera access is limited",
          body: "Use Chrome over HTTPS for the production capture flow.",
          tone: "warning",
        };

  return <StateCard title={copy.title} body={copy.body} tone={copy.tone} />;
}
