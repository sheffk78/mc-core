import { useState, useEffect, useCallback } from "react";
import {
  fetchUsers, createUser, updateUser, deleteUser,
  fetchBrands, createBrand, updateBrand, deleteBrand,
} from "@/lib/api";
import {
  Plus, Trash2, Pencil, Check, X, User, Palette, Tag,
  ChevronDown, ChevronUp, Settings2, Shield,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog";

const AVATAR_COLORS = [
  "#c85a2a", "#2d6a4f", "#1d3557", "#9b2226", "#6a4c93",
  "#457b9d", "#bc6c25", "#606c38", "#283618", "#003049",
];

function UserDialog({ open, onOpenChange, user, onSaved }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("human");
  const [email, setEmail] = useState("");
  const [color, setColor] = useState(AVATAR_COLORS[0]);
  const [saving, setSaving] = useState(false);
  const isEdit = !!user;

  useEffect(() => {
    if (open) {
      setName(user?.name || "");
      setRole(user?.role || "human");
      setEmail(user?.email || "");
      setColor(user?.avatar_color || AVATAR_COLORS[0]);
    }
  }, [open, user]);

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      if (isEdit) {
        await updateUser(user.id, { name, role, email, avatar_color: color });
      } else {
        await createUser({ name, role, email, avatar_color: color });
      }
      onOpenChange(false);
      if (onSaved) onSaved();
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
            {isEdit ? "Edit User" : "Add User"}
          </DialogTitle>
          <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
            {isEdit ? "Update user details." : "Add a new human or agent user."}
          </DialogDescription>
        </DialogHeader>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
          <div>
            <label className="mc-dialog-label">Name</label>
            <input className="mc-dialog-input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Jeff or Kit" data-testid="user-name-input" />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label className="mc-dialog-label">Role</label>
              <select className="mc-dialog-input" value={role} onChange={e => setRole(e.target.value)} data-testid="user-role-select">
                <option value="human">Human</option>
                <option value="agent">Agent</option>
              </select>
            </div>
            <div>
              <label className="mc-dialog-label">Email (optional)</label>
              <input className="mc-dialog-input" value={email} onChange={e => setEmail(e.target.value)} placeholder="user@example.com" data-testid="user-email-input" />
            </div>
          </div>
          <div>
            <label className="mc-dialog-label">Avatar Color</label>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
              {AVATAR_COLORS.map(c => (
                <button
                  key={c}
                  onClick={() => setColor(c)}
                  data-testid={`user-color-${c}`}
                  style={{
                    width: "28px", height: "28px", borderRadius: "50%", background: c,
                    border: color === c ? "3px solid var(--mc-ink)" : "2px solid var(--mc-rule)",
                    cursor: "pointer", transition: "border 150ms",
                  }}
                />
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <button className="mc-btn mc-btn-outline" onClick={() => onOpenChange(false)}>Cancel</button>
          <button className="mc-btn mc-btn-approve" onClick={handleSave} disabled={saving || !name.trim()} data-testid="user-save-btn">
            {saving ? "Saving..." : isEdit ? "Save" : "Add User"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function BrandDialog({ open, onOpenChange, brand, onSaved }) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [color, setColor] = useState("#8a8480");
  const [saving, setSaving] = useState(false);
  const isEdit = !!brand;

  useEffect(() => {
    if (open) {
      setName(brand?.name || "");
      setSlug(brand?.slug || "");
      setColor(brand?.color || "#8a8480");
    }
  }, [open, brand]);

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      if (isEdit) {
        await updateBrand(brand.slug, { name, color });
      } else {
        const s = slug.trim() || name.trim().toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
        await createBrand({ name: name.trim(), slug: s, color });
      }
      onOpenChange(false);
      if (onSaved) onSaved();
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
            {isEdit ? "Edit Brand" : "Add Brand"}
          </DialogTitle>
        </DialogHeader>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
          <div>
            <label className="mc-dialog-label">Brand Name</label>
            <input className="mc-dialog-input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Acme Corp" data-testid="brand-name-input" />
          </div>
          {!isEdit && (
            <div>
              <label className="mc-dialog-label">Slug (auto-generated if empty)</label>
              <input className="mc-dialog-input" value={slug} onChange={e => setSlug(e.target.value)} placeholder="acme-corp" data-testid="brand-slug-input" style={{ fontFamily: "monospace", fontSize: "12px" }} />
            </div>
          )}
          <div>
            <label className="mc-dialog-label">Brand Color</label>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
              <input type="color" value={color} onChange={e => setColor(e.target.value)} data-testid="brand-color-picker" style={{ width: "36px", height: "36px", padding: 0, border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)", cursor: "pointer" }} />
              <span style={{ fontFamily: "monospace", fontSize: "12px", color: "var(--mc-ink-3)" }}>{color}</span>
            </div>
          </div>
        </div>
        <DialogFooter>
          <button className="mc-btn mc-btn-outline" onClick={() => onOpenChange(false)}>Cancel</button>
          <button className="mc-btn mc-btn-approve" onClick={handleSave} disabled={saving || !name.trim()} data-testid="brand-save-btn">
            {saving ? "Saving..." : isEdit ? "Save" : "Add Brand"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function SettingsView({ onBrandsChanged }) {
  const [users, setUsers] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingBrands, setLoadingBrands] = useState(true);
  const [userDialog, setUserDialog] = useState({ open: false, user: null });
  const [brandDialog, setBrandDialog] = useState({ open: false, brand: null });
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [activeSection, setActiveSection] = useState("users");

  const loadUsers = useCallback(() => {
    setLoadingUsers(true);
    fetchUsers().then(setUsers).catch(console.error).finally(() => setLoadingUsers(false));
  }, []);

  const loadBrands = useCallback(() => {
    setLoadingBrands(true);
    fetchBrands().then(setBrands).catch(console.error).finally(() => setLoadingBrands(false));
  }, []);

  useEffect(() => { loadUsers(); loadBrands(); }, [loadUsers, loadBrands]);

  const handleDeleteUser = async (userId) => {
    try {
      await deleteUser(userId);
      setConfirmDelete(null);
      loadUsers();
    } catch (e) { console.error(e); }
  };

  const handleDeleteBrand = async (slug) => {
    try {
      await deleteBrand(slug);
      setConfirmDelete(null);
      loadBrands();
      if (onBrandsChanged) onBrandsChanged();
    } catch (e) { console.error(e); }
  };

  const sections = [
    { key: "users", label: "Users & Agents", Icon: User },
    { key: "brands", label: "Brands", Icon: Tag },
    { key: "general", label: "General", Icon: Settings2 },
  ];

  const filteredBrands = brands.filter(b => b.slug !== "all");

  return (
    <div data-testid="settings-view" style={{ display: "flex", gap: "24px" }}>
      {/* Settings nav */}
      <div style={{
        width: "180px", flexShrink: 0,
        borderRight: "1px solid var(--mc-rule)",
        paddingRight: "20px",
      }}>
        <h2 style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontSize: "22px", fontWeight: 500, color: "var(--mc-ink)",
          margin: "0 0 20px",
        }} data-testid="settings-heading">Settings</h2>
        {sections.map(s => (
          <button
            key={s.key}
            onClick={() => setActiveSection(s.key)}
            data-testid={`settings-nav-${s.key}`}
            style={{
              display: "flex", alignItems: "center", gap: "8px",
              width: "100%", textAlign: "left",
              padding: "8px 12px", marginBottom: "4px",
              borderRadius: "var(--mc-radius)",
              border: "none", cursor: "pointer",
              background: activeSection === s.key ? "var(--mc-accent-bg)" : "transparent",
              color: activeSection === s.key ? "var(--mc-accent)" : "var(--mc-ink-3)",
              fontSize: "12px", fontWeight: activeSection === s.key ? 600 : 400,
              fontFamily: "'Libre Franklin', sans-serif",
              transition: "background 150ms, color 150ms",
            }}
          >
            <s.Icon size={13} />
            {s.label}
          </button>
        ))}
      </div>

      {/* Settings content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Users section */}
        {activeSection === "users" && (
          <div data-testid="settings-users-section">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div>
                <h3 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500, margin: 0 }}>
                  Users & Agents
                </h3>
                <p style={{ fontSize: "12px", color: "var(--mc-ink-3)", marginTop: "2px" }}>
                  Manage the people and AI agents who can be assigned tasks.
                </p>
              </div>
              <button className="mc-btn mc-btn-approve" onClick={() => setUserDialog({ open: true, user: null })} data-testid="add-user-btn" style={{ gap: "6px" }}>
                <Plus size={12} /> Add User
              </button>
            </div>
            {loadingUsers ? (
              <div className="mc-empty">Loading...</div>
            ) : users.length === 0 ? (
              <div className="mc-empty" data-testid="no-users">No users yet</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {users.map(u => (
                  <div key={u.id} data-testid={`user-card-${u.id}`} style={{
                    display: "flex", alignItems: "center", gap: "14px",
                    padding: "14px 18px", background: "var(--mc-white)",
                    border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)",
                    transition: "border-color 150ms",
                  }}>
                    <div style={{
                      width: "36px", height: "36px", borderRadius: "50%",
                      background: u.avatar_color || "#c85a2a",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: "#fff", fontSize: "14px", fontWeight: 600,
                      fontFamily: "'Playfair Display', Georgia, serif",
                      flexShrink: 0,
                    }}>
                      {(u.name || "?")[0].toUpperCase()}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "13.5px", fontWeight: 500, color: "var(--mc-ink)" }}>{u.name}</div>
                      <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "2px" }}>
                        <span style={{
                          fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase",
                          letterSpacing: "0.08em",
                          color: u.role === "agent" ? "var(--mc-green)" : "var(--mc-ink-3)",
                        }}>
                          {u.role === "agent" ? (
                            <><Shield size={9} style={{ display: "inline", marginRight: "2px", verticalAlign: "-1px" }} />Agent</>
                          ) : "Human"}
                        </span>
                        {u.email && <span style={{ fontSize: "11px", color: "var(--mc-ink-4)" }}>{u.email}</span>}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "4px" }}>
                      <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => setUserDialog({ open: true, user: u })} data-testid={`edit-user-${u.id}`}>
                        <Pencil size={11} />
                      </button>
                      <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => setConfirmDelete({ type: "user", item: u })} data-testid={`delete-user-${u.id}`} style={{ color: "var(--mc-red, #c0392b)" }}>
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Brands section */}
        {activeSection === "brands" && (
          <div data-testid="settings-brands-section">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div>
                <h3 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500, margin: 0 }}>
                  Brands
                </h3>
                <p style={{ fontSize: "12px", color: "var(--mc-ink-3)", marginTop: "2px" }}>
                  Manage the brands and portfolios tracked in Mission Control.
                </p>
              </div>
              <button className="mc-btn mc-btn-approve" onClick={() => setBrandDialog({ open: true, brand: null })} data-testid="add-brand-btn" style={{ gap: "6px" }}>
                <Plus size={12} /> Add Brand
              </button>
            </div>
            {loadingBrands ? (
              <div className="mc-empty">Loading...</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {filteredBrands.map(b => (
                  <div key={b.slug} data-testid={`brand-card-${b.slug}`} style={{
                    display: "flex", alignItems: "center", gap: "14px",
                    padding: "14px 18px", background: "var(--mc-white)",
                    border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)",
                  }}>
                    <div style={{
                      width: "28px", height: "28px", borderRadius: "4px",
                      background: b.color, flexShrink: 0,
                    }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "13.5px", fontWeight: 500, color: "var(--mc-ink)" }}>{b.name}</div>
                      <div style={{ fontSize: "10.5px", color: "var(--mc-ink-4)", fontFamily: "monospace" }}>{b.slug}</div>
                    </div>
                    <div style={{ display: "flex", gap: "4px" }}>
                      <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => setBrandDialog({ open: true, brand: b })} data-testid={`edit-brand-${b.slug}`}>
                        <Pencil size={11} />
                      </button>
                      <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => setConfirmDelete({ type: "brand", item: b })} data-testid={`delete-brand-${b.slug}`} style={{ color: "var(--mc-red, #c0392b)" }}>
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* General section */}
        {activeSection === "general" && (
          <div data-testid="settings-general-section">
            <h3 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500, margin: "0 0 20px" }}>
              General
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{
                padding: "16px 20px", background: "var(--mc-white)",
                border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)",
              }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--mc-ink)", marginBottom: "4px" }}>Auto-Archive</div>
                <div style={{ fontSize: "11.5px", color: "var(--mc-ink-3)", lineHeight: 1.5 }}>
                  Completed tasks are automatically archived after 7 days and removed from the Kanban board. This keeps your workspace clean without losing history.
                </div>
              </div>
              <div style={{
                padding: "16px 20px", background: "var(--mc-white)",
                border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)",
              }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--mc-ink)", marginBottom: "4px" }}>AgentMail Sync</div>
                <div style={{ fontSize: "11.5px", color: "var(--mc-ink-3)", lineHeight: 1.5 }}>
                  Emails are synced from AgentMail every 2 minutes automatically. New emails appear as pending approvals in the queue.
                </div>
              </div>
              <div style={{
                padding: "16px 20px", background: "var(--mc-white)",
                border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)",
              }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--mc-ink)", marginBottom: "4px" }}>Real-Time Updates</div>
                <div style={{ fontSize: "11.5px", color: "var(--mc-ink-3)", lineHeight: 1.5 }}>
                  WebSocket connection provides live updates across all views. The status indicator in the sidebar and topbar shows connection state.
                </div>
              </div>
              <div style={{
                padding: "16px 20px", background: "var(--mc-white)",
                border: "1px solid var(--mc-rule)", borderRadius: "var(--mc-radius)",
              }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--mc-ink)", marginBottom: "4px" }}>API Version</div>
                <div style={{ fontSize: "11.5px", color: "var(--mc-ink-3)" }}>
                  All endpoints are served at <code style={{ fontFamily: "monospace", fontSize: "11px", background: "var(--mc-off-white)", padding: "1px 5px", borderRadius: "2px" }}>/api/v1/</code>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <UserDialog
        open={userDialog.open}
        onOpenChange={(v) => !v && setUserDialog({ open: false, user: null })}
        user={userDialog.user}
        onSaved={loadUsers}
      />
      <BrandDialog
        open={brandDialog.open}
        onOpenChange={(v) => !v && setBrandDialog({ open: false, brand: null })}
        brand={brandDialog.brand}
        onSaved={() => { loadBrands(); if (onBrandsChanged) onBrandsChanged(); }}
      />

      {/* Delete confirmation */}
      {confirmDelete && (
        <Dialog open onOpenChange={() => setConfirmDelete(null)}>
          <DialogContent className="sm:max-w-[380px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
            <DialogHeader>
              <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "16px" }}>
                Delete {confirmDelete.type === "user" ? "User" : "Brand"}
              </DialogTitle>
              <DialogDescription style={{ fontSize: "12px" }}>
                Are you sure you want to delete "<strong>{confirmDelete.item.name}</strong>"?
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <button className="mc-btn mc-btn-outline" onClick={() => setConfirmDelete(null)}>Cancel</button>
              <button
                className="mc-btn"
                onClick={() => confirmDelete.type === "user" ? handleDeleteUser(confirmDelete.item.id) : handleDeleteBrand(confirmDelete.item.slug)}
                data-testid="confirm-delete-btn"
                style={{ background: "var(--mc-red-bg)", color: "var(--mc-red, #c0392b)", border: "1px solid currentColor" }}
              >
                <Trash2 size={12} style={{ marginRight: "4px" }} /> Delete
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
