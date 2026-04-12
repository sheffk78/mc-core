import { useState } from "react";
import axios from "axios";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function EditDraftDialog({ open, onOpenChange, item, onSaved }) {
  const [toAddress, setToAddress] = useState(item.to_address || "");
  const [subject, setSubject] = useState(item.subject || "");
  const [body, setBody] = useState(item.preview || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const resp = await axios.patch(
        `${BACKEND_URL}/api/approvals/${item.id}`,
        { to_address: toAddress, subject, preview: body },
        { headers: { "Content-Type": "application/json" } }
      );
      if (onSaved) onSaved(resp.data);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[600px]"
        style={{ fontFamily: "'Libre Franklin', sans-serif", maxHeight: "85vh", overflow: "auto" }}
      >
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
            Edit Draft
          </DialogTitle>
          <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
            Review and edit before approving. Changes are saved to the draft.
          </DialogDescription>
        </DialogHeader>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
          {/* From (read-only) */}
          <div>
            <label className="mc-dialog-label">From</label>
            <div style={{
              fontSize: "13px",
              padding: "8px 12px",
              background: "var(--mc-warm-gray)",
              borderRadius: "var(--mc-radius)",
              color: "var(--mc-ink-2)",
            }}>
              {item.from_address} ({item.agent_name})
            </div>
          </div>

          {/* To */}
          <div>
            <label className="mc-dialog-label">To</label>
            <input
              className="mc-dialog-input"
              value={toAddress}
              onChange={e => setToAddress(e.target.value)}
              placeholder="recipient@example.com"
              data-testid="edit-draft-to"
            />
          </div>

          {/* Subject */}
          <div>
            <label className="mc-dialog-label">Subject</label>
            <input
              className="mc-dialog-input"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              data-testid="edit-draft-subject"
            />
          </div>

          {/* Body */}
          <div>
            <label className="mc-dialog-label">Body</label>
            <textarea
              className="mc-dialog-input"
              value={body}
              onChange={e => setBody(e.target.value)}
              data-testid="edit-draft-body"
              rows={10}
              style={{
                resize: "vertical",
                fontFamily: "'Libre Franklin', sans-serif",
                lineHeight: 1.6,
                minHeight: "160px",
              }}
            />
          </div>
        </div>

        <DialogFooter style={{ marginTop: "8px" }}>
          <button
            className="mc-btn mc-btn-outline"
            onClick={() => onOpenChange(false)}
            data-testid="edit-draft-cancel"
          >
            Cancel
          </button>
          <button
            className="mc-btn mc-btn-approve"
            onClick={handleSave}
            disabled={saving}
            data-testid="edit-draft-save"
          >
            {saving ? "Saving..." : "Save Draft"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
