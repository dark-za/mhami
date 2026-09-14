/** EvidencePage — capture, submit, issue, and discussion flows for a task. */

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

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

function formatDate(value: string, locale: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString(locale);
}

export function EvidencePage({ taskId, locale: _locale }: EvidencePageProps) {
  const { i18n, t } = useTranslation();
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
    })().catch((_error: unknown) => {
      setPanelError(t("evidence.load_failed"));
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
        setPanelError(t("evidence.camera_unavailable"));
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
    } catch (_error: unknown) {
      setPanelError(t("evidence.camera_failed"));
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
      setCaptureStatus(t("evidence.session_ready"));
    } catch (_error: unknown) {
      setPanelError(t("evidence.session_failed"));
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
      setCaptureStatus(t("evidence.submit_success"));
      const refreshed = await api<EvidenceTaskView>(`/api/v1/evidence/tasks/${taskId}`);
      setItems(refreshed.evidence ?? []);
      setIssues(refreshed.issues ?? []);
      setMessages(refreshed.messages ?? []);
    } catch (_error: unknown) {
      setPanelError(t("evidence.submit_failed"));
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
    } catch (_error: unknown) {
      setPanelError(t("evidence.issue_failed"));
    }
  }

  async function addMessage() {
    if (!issues[0]) {
      setPanelError(t("evidence.issue_required"));
      return;
    }
    try {
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
    } catch (_error: unknown) {
      setPanelError(t("evidence.message_failed"));
    }
  }

  if (!taskId) {
    return (
      <Panel eyebrow={t("evidence.title")} title={t("evidence.workspace")}>
        <p className="muted">{t("evidence.select_task")}</p>
      </Panel>
    );
  }

  function changeEvidenceType(nextType: string) {
    setEvidenceType(nextType);
    setCaptureToken("");
    setChallengeText("");
    setCaptureStatus(null);
    setCapturedBlob(null);
    setPreviewUrl("");
  }

  const isImageEvidence = evidenceType === "image";
  const needsNote = evidenceType === "note";
  const needsNumber = evidenceType === "number";
  const needsConfirmation = evidenceType === "confirmation";
  const evidenceReady =
    Boolean(captureToken) &&
    (!needsNote || noteText.trim().length > 0) &&
    (!needsNumber || numberValue.trim().length > 0) &&
    (!needsConfirmation || confirmationValue) &&
    (!isImageEvidence || Boolean(capturedBlob));

  return (
    <Panel eyebrow={t("evidence.title")} title={t("evidence.workspace")}>
      {panelError ? <p className="status status-danger">{panelError}</p> : null}
      {captureStatus ? <p className="status status-success">{captureStatus}</p> : null}
      <div className="evidence-intro">
        <label>
          <span>{t("evidence.type_label")}</span>
          <select value={evidenceType} onChange={(event) => changeEvidenceType(event.target.value)}>
            <option value="image">{t("evidence.type.image")}</option>
            <option value="number">{t("evidence.type.number")}</option>
            <option value="note">{t("evidence.type.note")}</option>
            <option value="confirmation">{t("evidence.type.confirmation")}</option>
          </select>
        </label>
        <div className="state-card">
          <strong>{t("evidence.selected_task")}</strong>
          <p className="muted">{t("evidence.selected_task_body")}</p>
        </div>
      </div>

      <section className="evidence-capture" aria-labelledby="capture-heading">
        <div className="section-heading"><div><p className="eyebrow">{t("evidence.step", { number: 1 })}</p><h3 id="capture-heading">{t("evidence.prepare_title")}</h3></div></div>
        <p className="muted">{t("evidence.prepare_body")}</p>
        <div className="inline-actions">
          <button className="primary-button" type="button" onClick={() => void requestCaptureSession()}>
            {captureToken ? t("evidence.refresh_session") : t("evidence.prepare_session")}
          </button>
        </div>

        {isImageEvidence ? (
          <div className="image-capture-area">
            <div className="inline-actions">
              <button className="ghost-button" type="button" onClick={() => void startCamera()}>{t("evidence.start_camera")}</button>
              <button className="ghost-button" type="button" onClick={() => void captureFrame()} disabled={!cameraReady}>{t("evidence.capture_frame")}</button>
            </div>
            <video ref={videoRef} className="camera-preview" playsInline muted autoPlay />
            {previewUrl ? <img className="camera-preview" src={previewUrl} alt={t("evidence.preview_alt")} /> : null}
          </div>
        ) : null}
      </section>

      <section className="evidence-capture" aria-labelledby="details-heading">
        <div className="section-heading"><div><p className="eyebrow">{t("evidence.step", { number: 2 })}</p><h3 id="details-heading">{t("evidence.details_title")}</h3></div></div>
        <div className="form-grid">
          {needsNote ? <label><span>{t("evidence.note_label")}</span><textarea required value={noteText} onChange={(event) => setNoteText(event.target.value)} /></label> : null}
          {needsNumber ? <label><span>{t("evidence.number_label")}</span><input className="bidi-ltr" dir="ltr" inputMode="decimal" required value={numberValue} onChange={(event) => setNumberValue(event.target.value)} /></label> : null}
          {needsConfirmation ? <label className="checkbox-field"><input type="checkbox" checked={confirmationValue} onChange={(event) => setConfirmationValue(event.target.checked)} /><span>{t("evidence.confirm_accuracy")}</span></label> : null}
          {isImageEvidence ? (
            <>
              <label><span>{t("evidence.challenge_response")}</span><input value={challengeResponse} onChange={(event) => setChallengeResponse(event.target.value)} /></label>
              <label className="checkbox-field"><input type="checkbox" checked={faceDetected} onChange={(event) => setFaceDetected(event.target.checked)} /><span>{t("evidence.face_detected")}</span></label>
            </>
          ) : null}
        </div>
        {challengeText ? <p className="muted">{t("evidence.challenge", { text: challengeText })}</p> : null}
        <div className="inline-actions">
          <button className="primary-button" type="button" onClick={() => void submitEvidence()} disabled={!evidenceReady}>
            {t("evidence.submit_evidence")}
          </button>
        </div>
      </section>
      <div className="notification-list">
        {items.map((item) => (
          <div key={item.id} className="notification-item">
            <strong>{t(`evidence.type.${item.evidence_type}`, { defaultValue: item.evidence_type })}</strong>
            <p>{item.note_text || t("evidence.no_note")}</p>
            <small>
              {t("evidence.risk", { score: item.duplicate_risk_score })} ·{" "}
              {item.face_detected ? t("evidence.face_detected") : t("evidence.face_not_detected")}
            </small>
          </div>
        ))}
      </div>
      <div className="form-stack">
        <label>
          <span>{t("evidence.issue_note")}</span>
          <input value={issueNote} onChange={(event) => setIssueNote(event.target.value)} />
        </label>
        <button className="ghost-button" type="button" onClick={() => void reportIssue()}>
          {t("evidence.report_issue")}
        </button>
      </div>
      <div className="form-stack">
        <label>
          <span>{t("evidence.discussion_message")}</span>
          <input
            value={discussionMessage}
            onChange={(event) => setDiscussionMessage(event.target.value)}
          />
        </label>
        <button className="ghost-button" type="button" onClick={() => void addMessage()}>
          {t("evidence.send_reply")}
        </button>
      </div>
      <div className="notification-list">
        {issues.map((issue) => (
          <div key={issue.id} className="notification-item">
            <strong>{issue.note}</strong>
            <small>{formatDate(issue.created_at, i18n.language)}</small>
          </div>
        ))}
        {messages.map((message) => (
          <div key={message.id} className="notification-item">
            <strong>{message.message}</strong>
            <small>{formatDate(message.created_at, i18n.language)}</small>
          </div>
        ))}
      </div>
    </Panel>
  );
}
