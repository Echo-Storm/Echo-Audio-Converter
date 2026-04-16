# Echo Audio Converter v0.5.3 — Third Audit Report

**Scope:** Full re-read of all source files post-v0.5.3 fixes  
**Status:** Four findings. One functional issue, one UX gap, two minor items.
The codebase is otherwise clean — no crashes, no data-loss paths, no bare excepts,
no dead code, no import noise.

---

## P1 — `main_window.py` — Update button stays clickable during network check

**File:** `ui/main_window.py`, `_on_update_clicked()`  
**Severity:** Low-medium — two concurrent update workers can start

```python
def _on_update_clicked(self):
    try:
        available, latest, installed = self.updater.is_update_available()  # ← network call
    except Exception as e:
        ...
    ...
    self.update_btn.setEnabled(False)   # ← only disabled here, after the call
```

`is_update_available()` makes an HTTP request with a 30-second timeout. During that
time `update_btn` is still enabled. A double-click fires two concurrent calls. If
both complete and the user confirms the second dialog, two `UpdateWorker` threads
start simultaneously — both downloading and writing over the same `ffmpeg.exe`.

**Fix:** Disable the button immediately, before any network I/O:

```python
def _on_update_clicked(self):
    self.update_btn.setEnabled(False)
    try:
        available, latest, installed = self.updater.is_update_available()
    except Exception as e:
        self.update_btn.setEnabled(True)
        QMessageBox.warning(...)
        return
    ...
    # On "No" or "Up to date", re-enable
```

---

## P2 — `main_window.py` — Dropping unsupported files gives no feedback

**File:** `ui/main_window.py`, `dropEvent()`  
**Severity:** Low — silent, confusing UX

```python
if files:
    self._add_files_to_queue(files, base_dir=base_dir)
# ← no else: dropping a folder of .txt files does nothing visibly
```

`_on_add_folder()` shows "No supported audio files found." for the same situation.
Dropping a folder of `.pdf` or `.txt` files is silently ignored — the status bar
doesn't change, the queue doesn't change. Users will think the drop didn't register.

**Fix:** Add the missing else branch:

```python
if files:
    self._add_files_to_queue(files, base_dir=base_dir)
else:
    self.status_bar.showMessage("No supported audio files in drop", 3000)
```

---

## P3 — `ffmpeg_wrapper.py:433` — Progress base is 0.15 even when analysis failed

**File:** `core/ffmpeg_wrapper.py`, `convert()`  
**Severity:** Low — cosmetic only

```python
progress_base = 0.15 if loudness_target is not None else 0.0
```

If analysis was requested but failed (e.g., timeout, corrupt file), `audio_filter`
is set to None and conversion proceeds without normalization. But `progress_base`
is still 0.15, so the progress bar jumps to 15% at the start of conversion as if
analysis had succeeded.

**Fix:** Base it on whether analysis actually produced a filter:

```python
progress_base = 0.15 if audio_filter is not None else 0.0
```

---

## P4 — `EchoAudioConverter.bat` — Existing venv never gets dependency updates

**File:** `EchoAudioConverter.bat`  
**Severity:** Low — affects users who run the bat before first checking a new release

```bat
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt
)
```

`pip install -r requirements.txt` only runs when creating a brand-new venv.
If a user already has a venv from a previous version, the bat skips the install
block entirely. A future `requirements.txt` update (new dependency, version bump)
would be silently ignored for existing installs.

**Fix:** Always run `pip install -r requirements.txt --quiet` outside the
creation block, so it runs on every launch and upgrades/adds as needed. Pip is
fast when everything is already satisfied.

---

## SUMMARY

| ID | File | Severity | Description |
|----|------|----------|-------------|
| P1 | main_window.py | Low-Med | Update button not disabled before blocking network call — allows double-invocation |
| P2 | main_window.py | Low | `dropEvent` gives no feedback when dropped files contain no supported audio |
| P3 | ffmpeg_wrapper.py | Low | `progress_base` 0.15 even when loudness analysis failed |
| P4 | EchoAudioConverter.bat | Low | Existing venv never gets `pip install` run on subsequent launches |

The codebase has reached a clean state. All previous medium/high severity issues
have been resolved across three passes. No crashes, no data-loss paths, no bare
excepts, no dead code, no import noise remain.
