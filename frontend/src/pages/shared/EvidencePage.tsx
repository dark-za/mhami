/** EvidencePage — capture, submit, issue, and discussion flows for a task. */

import { useEffect, useRef, useState } from "react";

import { api } from "../../api/client";
import type { Locale } from "../../design-system/tokens";
import { Panel } from "../../shell/ui";
import type {
  EvidenceIssueSummary,
  EvidenceMessageSummary,
  EvidenceSummary,
} from "../../domain";

interface EvidenceTaskView {
  evidence?: EvidenceSummary[];
  issues?: EvidenceIssueSummary[];
  messages?: EvidenceMessageSummary[];
}

export interface EvidencePageProps {
  taskId: string;
  locale: Locale;
}

export function EvidencePage({ taskId, locale: _locale }: EvidencePageProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [captureToken, setCaptureToken] = useState("");
  const [captureStatus, setCaptureStatus] = useState<string | null>(null);
  const [challengeText, setChallengeText] = useState("");
  const [evidenceType, setEvidenceType] = useState("image");
  const [noteText, setNoteText] = useState("");
  const [numberValue, setNumberValue] = useState("");
  const [confirmationValue, setConfirmationValue] = useState(false);
  const [faceDetected, setFaceDetected] = useState(true);
  const [challengeResponse, setChallengeResponse] = useState("");
  const [cameraReady, setCameraReady] = useState(false);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [items, setItems] = useState<EvidenceSummary[]>([]);
  const [issues, setIssues] = useState<EvidenceIssueSummary[]>([]);
  const [messages, setMessages] = useState<EvidenceMessageSummary[]>([]);
  const [issueNote, setIssueNote] = useState("");
  const [discussionMessage, setDiscussionMessage] = useState("");
  const [panelError, setPanelError] = useState<string | null>(null);

  useEffect(() => {
    setCaptureToken("");
    setChallengeText("");
    setCapturedBlob(null);
    setPreviewUrl("");
    setPanelError(null);
    setCaptureStatus(null);
    setIssueNote("");
    setDiscussionMessage("");
    if (!taskId) {
      setItems([]);
      setIssues([]);
      setMessages([]);
      return;
    }
    void (async () => {
      const payload = await api<EvidenceTaskView>(`/api/v1/evidence/tasks/${taskId}`);
      setItems(payload.evidence ?? []);
      setIssues(payload.issues ?? []);
      setMessages(payload.messages ?? []);
    })().catch((error: unknown) => {
      setPanelError(error instanceof Error ? error.message : "Could not load evidence.");
    });
  }, [taskId]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function startCamera() {
    try {
      if (!globalThis.navigator?.mediaDevices?.getUserMedia) {
        setPanelError("Camera is not available in this browser.");
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraReady(true);
    } catch (error: unknown) {
      setPanelError(error instanceof Error ? error.message : "Camera start failed.");
    }
  }

  async function captureFrame() {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((value) => resolve(value), "image/png", 0.92),
    );
    if (!blob) {
      return;
    }
    setCapturedBlob(blob);
    setPreviewUrl(URL.createObjectURL(blob));
  }

  async function requestCaptureSession() {
    try {
      setPanelError(null);
      const payload = await api<{ token: string; challenge_text?: string }>(
        "/api/v1/evidence/capture-sessions",
        {
          method: "POST",
          body: { task_instance_id: taskId, evidence_type: evidenceType },
        },
      );
      setCaptureToken(payload.token);
      setChallengeText(payload.challenge_text ?? "");
      setCaptureStatus("Capture session ready.");
    } catch (error: unknown) {
      setPanelError(error instanceof Error ? error.message : "Capture session failed.");
    }
  }

  async function submitEvidence() {
    try {
      setPanelError(null);
      const formData = new FormData();
      formData.set("capture_token", captureToken);
      formData.set("face_detected", String(faceDetected));
      formData.set("note_text", noteText);
      formData.set("challenge_response", challengeResponse);
      if (numberValue) {
        formData.set("number_value", numberValue);
      }
      formData.set("confirmation_value", String(confirmationValue));
      if (capturedBlob) {
        formData.set("file", new File([capturedBlob], "capture.png", { type: "image/png" }));
      }
      await api("/api/v1/evidence/submit", { method: "POST", body: formData });
      setCaptureStatus("Evidence submitted.");
      const refreshed = await api<EvidenceTaskView>(`/api/v1/evidence/tasks/${taskId}`);
      setItems(refreshed.evidence ?? []);
      setIssues(refreshed.issues ?? []);
      setMessages(refreshed.messages ?? []);
    } catch (error: unknown) {
      setPanelError(error instanceof Error ? error.message : "Submission failed.");
    }
  }

  async function reportIssue() {
    try {
      setPanelError(null);
      await api("/api/v1/evidence/issues", {
        method: "POST",
        body: { task_instance_id: taskId, note: issueNote },
      });
      setIssueNote("");
      const payload = await api<EvidenceTaskView>(`/api/v1/evidence/tasks/${taskId}`);
      setItems(payload.evidence ?? []);
      setIssues(payload.issues ?? []);
      setMessages(payload.messages ?? []);
    } catch (error: unknown) {
      setPanelError(error instanceof Error ? error.message : "Issue report failed.");
    }
  }

  async function addMessage() {
    try {
      if (!issues[0]) {
        throw new Error("Create an issue report first.");
      }
      await api(`/api/v1/evidence/issues/${issues[0].id}/messages`, {
        method: "POST",
        body: {
          task_instance_id: taskId,
          issue_report_id: issues[0].id,
          message: discussionMessage,
        },
      });
      setDiscussionMessage("");
      const payload = await api<EvidenceTaskView>(`/api/v1/evidence/tasks/${taskId}`);
      setMessages(payload.messages ?? []);
    } catch (error: unknown) {
      setPanelError(error instanceof Error ? error.message : "Discussion message failed.");
    }
  }

  if (!taskId) {
    return <p className="muted">Select a task to open the evidence workflow.</p>;
  }

  return (
    <Panel eyebrow="Evidence" title="Capture, submit, and discuss">
      {panelError ? <p className="status status-danger">{panelError}</p> : null}
      {captureStatus ? <p className="status status-success">{captureStatus}</p> : null}
      <div className="form-grid">
        <label>
          <span>Evidence type</span>
          <select value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)}>
            <option value="image">Image</option>
            <option value="number">Number</option>
            <option value="note">Note</option>
            <option value="confirmation">Confirmation</option>
          </select>
        </label>
        <label>
          <span>Task ID</span>
          <input value={taskId} readOnly />
        </label>
      </div>
      <div className="inline-actions">
        <button className="ghost-button" type="button" onClick={() => void startCamera()}>
          Start camera
        </button>
        <button
          className="ghost-button"
          type="button"
          onClick={() => void captureFrame()}
          disabled={!cameraReady}
        >
          Capture frame
        </button>
        <button
          className="ghost-button"
          type="button"
          onClick={() => void requestCaptureSession()}
        >
          New session
        </button>
      </div>
      <video ref={videoRef} className="camera-preview" playsInline muted autoPlay />
      {previewUrl ? (
        <img className="camera-preview" src={previewUrl} alt="Captured evidence preview" />
      ) : null}
      <div className="form-grid">
        <label>
          <span>Note</span>
          <input value={noteText} onChange={(event) => setNoteText(event.target.value)} />
        </label>
        <label>
          <span>Number</span>
          <input value={numberValue} onChange={(event) => setNumberValue(event.target.value)} />
        </label>
        <label>
          <span>Challenge response</span>
          <input
            value={challengeResponse}
            onChange={(event) => setChallengeResponse(event.target.value)}
          />
        </label>
        <label>
          <span>Confirmation</span>
          <input
            type="checkbox"
            checked={confirmationValue}
            onChange={(event) => setConfirmationValue(event.target.checked)}
          />
        </label>
      </div>
      <label>
        <span>Face detected</span>
        <input
          type="checkbox"
          checked={faceDetected}
          onChange={(event) => setFaceDetected(event.target.checked)}
        />
      </label>
      {challengeText ? <p className="muted">Challenge: {challengeText}</p> : null}
      <div className="inline-actions">
        <button className="primary-button" type="button" onClick={() => void submitEvidence()}>
          Submit evidence
        </button>
      </div>
      <div className="notification-list">
        {items.map((item) => (
          <div key={item.id} className="notification-item">
            <strong>{item.evidence_type}</strong>
            <p>{item.note_text || "No note"}</p>
            <small>
              Risk {item.duplicate_risk_score} ·{" "}
              {item.face_detected ? "face blurred" : "no face"}
            </small>
          </div>
        ))}
      </div>
      <div className="form-stack">
        <label>
          <span>Issue note</span>
          <input value={issueNote} onChange={(event) => setIssueNote(event.target.value)} />
        </label>
        <button className="ghost-button" type="button" onClick={() => void reportIssue()}>
          Report issue
        </button>
      </div>
      <div className="form-stack">
        <label>
          <span>Discussion message</span>
          <input
            value={discussionMessage}
            onChange={(event) => setDiscussionMessage(event.target.value)}
          />
        </label>
        <button className="ghost-button" type="button" onClick={() => void addMessage()}>
          Send reply
        </button>
      </div>
      <div className="notification-list">
        {issues.map((issue) => (
          <div key={issue.id} className="notification-item">
            <strong>{issue.note}</strong>
            <small>{issue.created_at}</small>
          </div>
        ))}
        {messages.map((message) => (
          <div key={message.id} className="notification-item">
            <strong>{message.message}</strong>
            <small>{message.created_at}</small>
          </div>
        ))}
      </div>
    </Panel>
  );
}
