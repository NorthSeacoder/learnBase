import hashlib
import io
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import closing, redirect_stdout
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from tools.learnbase import (
    ANKI_READ_ACTIONS,
    add_anki_mapping,
    add_source,
    add_topic,
    anki_decks,
    list_anki_mappings,
    remove_anki_mapping,
    main,
    create_note,
    project_profile,
    preview_anki,
    render_profile,
    save_evidence_status,
    save_card_proposal,
    save_profile_dimension,
    save_review_proposal,
    save_topic_proposal,
    setup_workspace,
    validate_card,
    validate_note,
    write_profile_report,
)


class LearnBaseCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        setup_workspace(self.root, "Test Space")
        add_topic(self.root, "biology", "Biology", None)

    def tearDown(self):
        self.tmp.cleanup()

    def dimension_proposal(self, topic_id="biology", dimension_id="derivation", minimum=2, recency_days=7):
        return {
            "proposal_version": 1,
            "topic_id": topic_id,
            "dimension_id": dimension_id,
            "name": "Derivation practice",
            "description": "Derives a result from stated premises",
            "eligible_activity_types": ["question_attempt", "recall_practice", "reading_observation", "practice_reflection"],
            "eligible_evidence_types": ["learner_statement", "observed_artifact", "verified_outcome"],
            "minimum_evidence_count": minimum,
            "recency_days": recency_days,
        }

    def review_proposal(self, key, direction="supports", occurred_at="2026-11-09T12:00:00Z", status="confirmed", activity_type="question_attempt", sources=None, notes=None, evidence_type="learner_statement"):
        input_fields = {
            "question_attempt": {"prompt": "Derive the result", "learner_response": "I used the stated premises"},
            "recall_practice": {"prompt": "Recall the rule", "recall": "I recalled the rule"},
            "reading_observation": {"observation": "The example uses substitution"},
            "practice_reflection": {"task": "Derive the result", "action": "Substituted the premises"},
        }
        evidence = {
            "evidence_type": evidence_type,
            "statement": f"Evidence recorded for {key}",
            "status": status,
            "dimensions": [{"dimension_id": "derivation", "direction": direction}],
            "sources": sources or [],
            "notes": notes or [],
        }
        proposal = {
            "proposal_version": 1,
            "idempotency_key": key,
            "topic_id": "biology",
            "activity_type": activity_type,
            "learner_input": input_fields[activity_type],
            "evidence": [evidence],
        }
        if occurred_at is not ...:
            proposal["occurred_at"] = occurred_at
        return proposal

    def card_fixture(self, suffix="one"):
        source = self.root / "01-sources" / f"{suffix}.pdf"
        source.write_bytes(f"source {suffix}".encode())
        add_source(self.root, "pdf", f"Source {suffix}", str(source), ["biology"])
        source_id = "SRC-0001" if suffix == "one" else "SRC-0002"
        note = create_note(self.root, f"Note {suffix}", ["biology"], [source_id], [f"{source_id}=page:2"])
        activity_id = save_review_proposal(self.root, {
            "proposal_version": 1,
            "idempotency_key": f"card-evidence-{suffix}",
            "topic_id": "biology",
            "activity_type": "question_attempt",
            "learner_input": {"prompt": "What is the rule?", "learner_response": "A learner answer"},
            "evidence": [{
                "evidence_type": "learner_statement",
                "statement": f"Reviewed evidence from {suffix}",
                "status": "confirmed",
                "dimensions": [],
                "sources": [{"source_id": source_id, "locator": "page:2"}],
                "notes": [note.stem[-9:]],
            }],
        }, approved=True)
        return note, activity_id, "EVD-0001" if suffix == "one" else "EVD-0002", source_id

    def card_proposal(self, note_id="NOTE-0001", evidence_id="EVD-0001", **overrides):
        proposal = {
            "proposal_version": 1,
            "topic_id": "biology",
            "objective_key": "cell-membrane-function",
            "front": "What is the function of the cell membrane?",
            "back": "It regulates movement of substances into and out of the cell.",
            "note_ids": [note_id],
            "evidence_ids": [evidence_id],
        }
        proposal.update(overrides)
        return proposal

    def start_anki_mock(self, response_for):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(payload)
                status, result = response_for(payload)
                body = json.dumps(result).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, requests

    def test_source_to_note_keeps_provenance(self):
        pdf = self.root / "01-sources" / "chapter.pdf"
        pdf.write_bytes(b"test PDF placeholder")
        add_source(self.root, "pdf", "Chapter", str(pdf), ["biology"])
        note = create_note(self.root, "Cell structure", ["biology"], ["SRC-0001"], ["SRC-0001=page:2"])
        validate_note(self.root, note.relative_to(self.root).as_posix())
        text = note.read_text(encoding="utf-8")
        self.assertIn("id: SRC-0001", text)
        self.assertIn("locator: \"page:2\"", text)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            source = conn.execute("SELECT source_mode, sha256 FROM sources").fetchone()
        self.assertEqual(source[0], "workspace")
        self.assertEqual(len(source[1]), 64)

    def test_external_pdf_is_registered_read_only_without_copy(self):
        external = self.root.parent / f"{self.root.name}-outside.pdf"
        external.write_bytes(b"external")
        try:
            add_source(self.root, "pdf", "External", str(external), ["biology"])
            with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
                row = conn.execute("SELECT source_mode, locator FROM sources").fetchone()
            self.assertEqual(row[0], "external-readonly")
            self.assertEqual(row[1], str(external.resolve()))
            self.assertTrue(external.exists())
        finally:
            external.unlink(missing_ok=True)

    def test_reimport_reuses_source_id_and_links_topic(self):
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"test")
        add_topic(self.root, "chemistry", "Chemistry", None)
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        add_source(self.root, "pdf", "Chapter", str(source), ["chemistry"])
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            topics = conn.execute("SELECT COUNT(*) FROM source_topics WHERE source_id = 'SRC-0001'").fetchone()[0]
        self.assertEqual(sources, 1)
        self.assertEqual(topics, 2)

    def test_changed_source_revision_is_not_silently_replaced(self):
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"original")
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        source.write_bytes(b"revised")
        with self.assertRaisesRegex(ValueError, "content changed"):
            add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            count, digest = conn.execute("SELECT COUNT(*), MAX(sha256) FROM sources").fetchone()
        self.assertEqual(count, 1)
        self.assertEqual(digest, hashlib.sha256(b"original").hexdigest())

    def test_note_validation_rejects_unregistered_citation(self):
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"test")
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        note = create_note(self.root, "Cell structure", ["biology"], ["SRC-0001"], [])
        note.write_text(note.read_text(encoding="utf-8").replace("SRC-0001", "SRC-9999"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "do not match"):
            validate_note(self.root, note.relative_to(self.root).as_posix())

    def test_existing_note_is_never_removed_on_collision(self):
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"test")
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        note = create_note(self.root, "Cell structure", ["biology"], ["SRC-0001"], [])
        original = note.read_text(encoding="utf-8")
        collision = self.root / "02-notes" / "biology" / f"{date.today().isoformat()}-NOTE-0002.md"
        collision.write_text("keep this file", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            create_note(self.root, "Another title", ["biology"], ["SRC-0001"], [])
        self.assertEqual(note.read_text(encoding="utf-8"), original)
        self.assertEqual(collision.read_text(encoding="utf-8"), "keep this file")

    def test_cli_source_to_note_commands(self):
        cli = Path(__file__).parents[1] / "tools" / "learnbase.py"
        def run(*args):
            return subprocess.run([sys.executable, str(cli), *args], cwd=self.root, text=True, capture_output=True, check=True)

        (self.root / "01-sources" / "article.pdf").write_bytes(b"pdf")
        run("source", "add", "pdf", "--path", "01-sources/article.pdf", "--title", "Chapter", "--topic", "biology")
        result = run("note", "new", "--title", "Cell structure", "--topic", "biology", "--source", "SRC-0001", "--locator", "SRC-0001=page:2")
        note_path = result.stdout.strip().split("created ", 1)[1]
        self.assertTrue((self.root / note_path).is_file())
        run("note", "validate", note_path)

    def test_approved_card_draft_persists_markdown_and_traceable_links(self):
        self.card_fixture()
        proposal = self.card_proposal()
        with self.assertRaisesRegex(ValueError, "obtain learner approval"):
            save_card_proposal(self.root, proposal, approved=False)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0], 0)

        card_id = save_card_proposal(self.root, proposal, approved=True)
        row = list((self.root / "04-cards" / "drafts" / "biology").glob("*.md"))[0]
        parsed = validate_card(self.root, row.relative_to(self.root).as_posix())
        self.assertEqual(card_id, "CARD-0001")
        self.assertEqual(parsed["notes"], ["NOTE-0001"])
        self.assertEqual(parsed["evidence"], ["EVD-0001"])
        self.assertEqual(parsed["sources"], [{"id": "SRC-0001", "locator": "page:2"}])
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(cards)")}
            source_links = conn.execute("SELECT source_id, locator FROM card_sources WHERE card_id = ?", (card_id,)).fetchall()
        self.assertNotIn("front", columns)
        self.assertNotIn("back", columns)
        self.assertEqual(source_links, [("SRC-0001", "page:2")])

    def test_card_merge_unions_provenance_idempotently_and_rejects_content_conflict(self):
        self.card_fixture("one")
        self.card_fixture("two")
        card_id = save_card_proposal(self.root, self.card_proposal(), approved=True)
        second = self.card_proposal(
            note_id="NOTE-0002", evidence_id="EVD-0002", card_id=card_id,
        )
        self.assertEqual(save_card_proposal(self.root, second, approved=True), card_id)
        self.assertEqual(save_card_proposal(self.root, second, approved=True), card_id)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            notes = conn.execute("SELECT note_id FROM card_notes WHERE card_id = ? ORDER BY note_id", (card_id,)).fetchall()
            sources = conn.execute("SELECT source_id, locator FROM card_sources WHERE card_id = ? ORDER BY source_id", (card_id,)).fetchall()
            count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        self.assertEqual(notes, [("NOTE-0001",), ("NOTE-0002",)])
        self.assertEqual(sources, [("SRC-0001", "page:2"), ("SRC-0002", "page:2")])
        self.assertEqual(count, 1)

        conflicting = dict(second, front="A different question")
        with self.assertRaisesRegex(ValueError, "conflicts with the existing objective"):
            save_card_proposal(self.root, conflicting, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM card_notes WHERE card_id = ?", (card_id,)).fetchone()[0], 2)

    def test_card_proposal_rejects_unlinked_evidence_and_cli_validation(self):
        self.card_fixture()
        invalid = self.card_proposal(evidence_id="EVD-9999")
        with self.assertRaisesRegex(ValueError, "not registered under topic"):
            save_card_proposal(self.root, invalid, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0], 0)

        cli = Path(__file__).parents[1] / "tools" / "learnbase.py"
        proposal_path = self.root / "card-proposal.json"
        proposal_path.write_text(json.dumps(self.card_proposal()), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(cli), "card", "draft", "save", "--proposal", str(proposal_path), "--approved"],
            cwd=self.root, text=True, capture_output=True, check=True,
        )
        card_path = result.stdout.strip().split("(", 1)[1].rstrip(")")
        subprocess.run(
            [sys.executable, str(cli), "card", "draft", "validate", card_path],
            cwd=self.root, text=True, capture_output=True, check=True,
        )

    def test_anki_preview_uses_only_read_actions_and_classifies_existing_basic_notes(self):
        self.card_fixture()
        note_fields = [
            ("What is Q1?", "Answer 1"),
            ("What is Q2?", "Different answer"),
        ]
        for index, (front, back) in enumerate([
            ("What is Q1?", "Answer 1"),
            ("What is Q2?", "Answer 2"),
            ("What is Q3?", "Answer 3"),
        ]):
            proposal = self.card_proposal(
                objective_key=f"objective-{index + 1}", front=front, back=back,
            )
            save_card_proposal(self.root, proposal, approved=True)

        existing = [
            {"noteId": 101 + index, "modelName": "Basic", "fields": {"Front": {"value": f"<div>{front}</div>"}, "Back": {"value": back}}}
            for index, (front, back) in enumerate(note_fields)
        ]

        def response_for(request):
            action = request["action"]
            if action == "deckNames":
                result = ["Biology", "Shared"]
            elif action == "modelNames":
                result = ["Basic", "Cloze"]
            elif action == "modelFieldNames":
                result = ["Front", "Back"]
            elif action == "findNotes":
                self.assertIn('deck:"Biology"', request["params"]["query"])
                result = [101, 102]
            elif action == "notesInfo":
                result = existing
            else:
                raise AssertionError(f"unexpected AnkiConnect action: {action}")
            return 200, {"result": result, "error": None}

        server, thread, requests = self.start_anki_mock(response_for)
        try:
            with patch("tools.learnbase.ANKI_CONNECT_PORT", server.server_address[1]):
                self.assertEqual(anki_decks(self.root), ["Biology", "Shared"])
                add_anki_mapping(self.root, "biology", "Biology")
                add_topic(self.root, "chemistry", "Chemistry", None)
                add_anki_mapping(self.root, "biology", "Shared")
                add_anki_mapping(self.root, "chemistry", "Shared")
                add_anki_mapping(self.root, "biology", "Shared")
                self.assertEqual(len(list_anki_mappings(self.root)), 3)
                remove_anki_mapping(self.root, "biology", "Shared")
                previews = preview_anki(self.root, "biology")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual([row["status"] for row in previews], ["already_present", "conflict", "proposed_addition"])
        self.assertEqual(previews[0]["front"], "What is Q1?")
        self.assertEqual(previews[0]["evidence"], {"EVD-0001": "confirmed"})
        self.assertEqual(previews[0]["sources"], [{"id": "SRC-0001", "locator": "page:2"}])
        self.assertTrue(previews[0]["read_only"])
        self.assertIn("subdecks", previews[0]["deck_scope"])
        self.assertTrue(requests)
        self.assertTrue(all(request["action"] in ANKI_READ_ACTIONS for request in requests))
        self.assertTrue(all(request["version"] == 6 for request in requests))
        self.assertTrue(all(set(request) == {"action", "version", "params"} for request in requests))

    def test_anki_adapter_works_without_configuration_and_rejects_writes_and_errors(self):
        from tools.learnbase import _ankiconnect_request

        with self.assertRaisesRegex(ValueError, "not allowed"):
            _ankiconnect_request("addNote", {})
        self.assertFalse((self.root / "learnbase.toml").exists())
        with patch("tools.learnbase._ankiconnect_request", return_value=["Biology"]) as request:
            self.assertEqual(anki_decks(self.root), ["Biology"])
            request.assert_called_once_with("deckNames")

        server, thread, _ = self.start_anki_mock(
            lambda request: (200, {"result": None, "error": "collection unavailable"})
        )
        try:
            with patch("tools.learnbase.ANKI_CONNECT_PORT", server.server_address[1]):
                with self.assertRaisesRegex(ValueError, "collection unavailable"):
                    anki_decks(self.root)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_card_replay_replacement_and_failed_write_preserve_local_state(self):
        self.card_fixture()
        proposal = self.card_proposal(front="Line 1\nLine 2")
        card_id = save_card_proposal(self.root, proposal, approved=True)
        card_file = next((self.root / "04-cards/drafts/biology").glob("*.md"))
        snapshot = card_file.read_bytes()
        with patch("tools.learnbase.now", return_value="2027-01-01T00:00:00+00:00"):
            save_card_proposal(self.root, proposal, approved=True)
        self.assertEqual(card_file.read_bytes(), snapshot)

        changed = dict(proposal, front="Line 1 Line 2")
        with self.assertRaisesRegex(ValueError, "conflicts"):
            save_card_proposal(self.root, changed, approved=True)
        changed.update(card_id=card_id, replace_content=True)
        save_card_proposal(self.root, changed, approved=True)
        self.assertEqual(validate_card(self.root, card_file.relative_to(self.root).as_posix())["front"], "Line 1 Line 2")

        self.card_fixture("two")
        merging = self.card_proposal(note_id="NOTE-0002", evidence_id="EVD-0002", front="Line 1 Line 2")
        with self.assertRaisesRegex(ValueError, "explicit card_id"):
            save_card_proposal(self.root, merging, approved=True)
        merging["card_id"] = card_id
        snapshot = card_file.read_bytes()
        with patch("tools.learnbase.os.replace", side_effect=OSError("injected replace failure")):
            with self.assertRaisesRegex(OSError, "injected"):
                save_card_proposal(self.root, merging, approved=True)
        self.assertEqual(card_file.read_bytes(), snapshot)
        with closing(sqlite3.connect(self.root / "data/learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM card_notes").fetchone()[0], 1)
        self.assertEqual(list(card_file.parent.glob("*.tmp")), [])

    def test_card_file_collision_bad_note_and_invalid_proposals_never_write_rows(self):
        note, _, _, _ = self.card_fixture()
        proposal = self.card_proposal()
        for patch_values in ({"proposal_version": True}, {"replace_content": True}, {"front": "## Back\nInjected"}, {"note_ids": []}):
            with self.subTest(values=patch_values), self.assertRaises(ValueError):
                save_card_proposal(self.root, dict(proposal, **patch_values), approved=True)
        note.write_text(note.read_text().replace("SRC-0001", "SRC-9999"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "citations"):
            save_card_proposal(self.root, proposal, approved=True)
        note.write_text(note.read_text().replace("SRC-9999", "SRC-0001"), encoding="utf-8")
        card_dir = self.root / "04-cards/drafts/biology"
        card_dir.mkdir()
        collision = card_dir / f"{date.today().isoformat()}-CARD-0001.md"
        collision.write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            save_card_proposal(self.root, proposal, approved=True)
        self.assertEqual(collision.read_text(), "keep me")
        collision.unlink()
        with patch("tools.learnbase.os.link", side_effect=OSError("injected link failure")):
            with self.assertRaisesRegex(OSError, "injected"):
                save_card_proposal(self.root, proposal, approved=True)
        with closing(sqlite3.connect(self.root / "data/learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0], 0)

    def test_card_merge_preserves_multiple_locators_and_rolls_back_failed_commit(self):
        self.card_fixture()
        card_id = save_card_proposal(self.root, self.card_proposal(), approved=True)
        create_note(self.root, "Same source, another page", ["biology"], ["SRC-0001"], ["SRC-0001=page:9"])
        merging = self.card_proposal(note_id="NOTE-0002", card_id=card_id)
        card_file = next((self.root / "04-cards/drafts/biology").glob("*.md"))
        before = card_file.read_bytes()

        class FailedCommit(sqlite3.Connection):
            def commit(self):
                raise sqlite3.OperationalError("injected commit failure")

        def failed_connection(root):
            connection = sqlite3.connect(root / "data/learnbase.sqlite3", factory=FailedCommit)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection

        with patch("tools.learnbase.connect", side_effect=failed_connection):
            with self.assertRaisesRegex(sqlite3.OperationalError, "injected commit"):
                save_card_proposal(self.root, merging, approved=True)
        self.assertEqual(card_file.read_bytes(), before)
        with closing(sqlite3.connect(self.root / "data/learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM card_notes").fetchone()[0], 1)
        save_card_proposal(self.root, merging, approved=True)
        parsed = validate_card(self.root, card_file.relative_to(self.root).as_posix())
        self.assertEqual(parsed["sources"], [{"id": "SRC-0001", "locator": "page:2"}, {"id": "SRC-0001", "locator": "page:9"}])

    def test_card_topic_ownership_tamper_and_path_escape_are_rejected(self):
        self.card_fixture()
        add_topic(self.root, "chemistry", "Chemistry", None)
        with self.assertRaisesRegex(ValueError, "not registered under topic chemistry"):
            save_card_proposal(self.root, self.card_proposal(topic_id="chemistry"), approved=True)
        card_id = save_card_proposal(self.root, self.card_proposal(), approved=True)
        card_file = next((self.root / "04-cards/drafts/biology").glob("*.md"))
        original = card_file.read_text()
        for content in (original.replace('"locator": "page:2"', '"locator": 8'), original.replace("## Back", "## Front"), original.replace("id: CARD-0001", "id: CARD-0001\nid: CARD-0001")):
            card_file.write_text(content, encoding="utf-8")
            with self.subTest(content=content), self.assertRaises(ValueError):
                validate_card(self.root, card_file.relative_to(self.root).as_posix())
        card_file.write_text(original, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inside 04-cards/drafts"):
            validate_card(self.root, "../outside.md")
        with tempfile.TemporaryDirectory() as outside:
            (self.root / "04-cards/drafts/chemistry").symlink_to(outside, target_is_directory=True)
            proposal = self.card_proposal(objective_key="different-objective")
            # A topic path symlink must not direct newly created card files outside the workspace.
            (self.root / "04-cards/drafts/biology").rename(self.root / "04-cards/drafts/saved")
            (self.root / "04-cards/drafts/biology").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "inside 04-cards/drafts"):
                save_card_proposal(self.root, proposal, approved=True)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_anki_cli_preview_returns_reviewable_json_without_local_mutations(self):
        self.card_fixture()
        save_card_proposal(self.root, self.card_proposal(), approved=True)
        before = (self.root / "data/learnbase.sqlite3").read_bytes()
        output = io.StringIO()
        with redirect_stdout(output), patch("tools.learnbase._ankiconnect_request", side_effect=[["Biology"], ["Basic"], ["Front", "Back"], []]):
            result = main(["--workspace", str(self.root), "anki", "preview", "--topic", "biology", "--deck", "Biology"])
        self.assertEqual(result, 0)
        preview = json.loads(output.getvalue())
        self.assertEqual(preview[0]["status"], "proposed_addition")
        self.assertIn("back", preview[0])
        self.assertEqual((self.root / "data/learnbase.sqlite3").read_bytes(), before)

    def test_flashcard_skill_and_host_links_preserve_read_only_contract(self):
        repository = Path(__file__).parents[1]
        canonical = repository / ".agents/skills/learnbase-flashcards"
        skill = (canonical / "SKILL.md").read_text(encoding="utf-8")
        for host in (".workbuddy", ".claude", ".cursor"):
            link = repository / host / "skills/learnbase-flashcards"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), canonical.resolve())
        for contract in ("supported by default", "nmem m search", "replace_content", "--approved", "transient", "no publish", "not source IDs"):
            # Check executable guidance boundaries; conversational quality is assessed by review.
            self.assertIn(contract, skill)

    def test_anki_malformed_transport_and_preview_results_fail_without_writes(self):
        from tools.learnbase import _ankiconnect_request
        for body in (b"broken-json", b'{}', b'{"error":null,"result":[]} extra'):
            with self.subTest(body=body), patch("tools.learnbase.http.client.HTTPConnection") as connection:
                response = connection.return_value.getresponse.return_value
                response.status = 200
                response.getheader.return_value = str(len(body))
                response.read.return_value = body
                with self.assertRaises(ValueError):
                    _ankiconnect_request("deckNames")
                connection.assert_called_with("127.0.0.1", 8765, timeout=2)
                connection.return_value.close.assert_called_once()
        with patch("tools.learnbase.http.client.HTTPConnection") as connection:
            connection.return_value.request.side_effect = TimeoutError("injected timeout")
            with self.assertRaisesRegex(ValueError, "unavailable"):
                _ankiconnect_request("deckNames")
        self.card_fixture()
        save_card_proposal(self.root, self.card_proposal(), approved=True)
        with patch("tools.learnbase._ankiconnect_request", side_effect=[["Biology"], ["Basic"], ["Front", "Back"], [101], [{}]]):
            with self.assertRaisesRegex(ValueError, "all requested note IDs"):
                preview_anki(self.root, "biology", "Biology")
        save_evidence_status(self.root, {"proposal_version": 1, "evidence_id": "EVD-0001", "status": "conflicting", "reason": "Learner disputes this evidence"}, approved=True)
        with patch("tools.learnbase._ankiconnect_request", side_effect=[["Biology"], ["Basic"], ["Front", "Back"], []]):
            result = preview_anki(self.root, "biology", "Biology")
        self.assertEqual(result[0]["status"], "skipped")
        self.assertIn("conflicting", result[0]["reason"])

    def test_fresh_workspace_commands_cover_web_intake(self):
        cli = Path(__file__).parents[1] / "tools" / "learnbase.py"
        workspace = self.root / "fresh-workspace"
        workspace.mkdir()
        def run(*args):
            return subprocess.run([sys.executable, str(cli), *args], cwd=workspace, text=True, capture_output=True, check=True)

        run("setup", "--name", "Reading Notes")
        run("topic", "add", "history", "--name", "History")
        run("source", "add", "web", "--url", "https://example.org/article", "--title", "An article", "--topic", "history")
        note_path = run("note", "new", "--title", "Article notes", "--topic", "history", "--source", "SRC-0001", "--locator", "SRC-0001=heading:Context").stdout.strip().split("created ", 1)[1]
        run("note", "validate", note_path)

    def test_setup_rerun_preserves_name_and_existing_rows(self):
        setup_workspace(self.root)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            name, topics = conn.execute("SELECT value, (SELECT COUNT(*) FROM topics) FROM metadata WHERE key = 'workspace_name'").fetchone()
        self.assertEqual(name, "Test Space")
        self.assertEqual(topics, 1)

        setup_workspace(self.root, "Renamed Space")
        setup_workspace(self.root)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            name, topics = conn.execute("SELECT value, (SELECT COUNT(*) FROM topics) FROM metadata WHERE key = 'workspace_name'").fetchone()
        self.assertEqual(name, "Renamed Space")
        self.assertEqual(topics, 1)

    def test_setup_upgrades_v1_database_without_losing_rows(self):
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"existing source")
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            conn.execute("DROP TABLE topic_config")
            conn.execute("UPDATE metadata SET value = '1' WHERE key = 'schema_version'")
            conn.commit()

        setup_workspace(self.root)

        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            version = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()[0]
            topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            config_table = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'topic_config'").fetchone()
        self.assertEqual(version, "4")
        self.assertEqual(topics, 1)
        self.assertEqual(sources, 1)
        self.assertIsNotNone(config_table)

    def test_setup_upgrades_populated_v2_database_without_losing_rows(self):
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"v2 source")
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        note = create_note(self.root, "Cell structure", ["biology"], ["SRC-0001"], ["SRC-0001=page:2"])
        save_topic_proposal(self.root, {
            "proposal_version": 1,
            "topic_id": "astronomy",
            "name": "Astronomy",
            "learning_goal": "Understand stars",
        }, approved=True)
        db_path = self.root / "data" / "learnbase.sqlite3"
        with closing(sqlite3.connect(db_path)) as conn:
            for table in (
                "card_sources",
                "card_evidence",
                "card_notes",
                "topic_anki_decks",
                "cards",
                "evidence_status_history",
                "evidence_notes",
                "evidence_sources",
                "evidence_dimensions",
                "learning_evidence",
                "topic_profile_dimensions",
                "learning_activities",
            ):
                conn.execute(f"DROP TABLE {table}")
            conn.execute("UPDATE metadata SET value = '2' WHERE key = 'schema_version'")
            conn.commit()

        setup_workspace(self.root)

        with closing(sqlite3.connect(db_path)) as conn:
            version = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()[0]
            topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            notes = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            configs = conn.execute("SELECT COUNT(*) FROM topic_config").fetchone()[0]
            new_tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN "
                "('learning_activities', 'learning_evidence', 'topic_profile_dimensions', 'evidence_status_history', "
                "'cards', 'card_notes', 'card_evidence', 'card_sources', 'topic_anki_decks')"
            ).fetchone()[0]
        self.assertEqual((version, topics, sources, notes, configs), ("4", 2, 1, 1, 1))
        self.assertEqual(new_tables, 9)
        self.assertTrue(note.is_file())

    def test_setup_rejects_future_schema_without_downgrade(self):
        db_path = self.root / "data" / "learnbase.sqlite3"
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("UPDATE metadata SET value = '99' WHERE key = 'schema_version'")
            conn.commit()
        with self.assertRaisesRegex(ValueError, "newer than supported"):
            setup_workspace(self.root)
        with closing(sqlite3.connect(db_path)) as conn:
            version = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()[0]
        self.assertEqual(version, "99")

    def test_review_write_requires_approval_and_idempotency_digest(self):
        save_profile_dimension(self.root, self.dimension_proposal(), approved=True)
        proposal = self.review_proposal("attempt-001")
        with self.assertRaisesRegex(ValueError, "obtain learner approval"):
            save_review_proposal(self.root, proposal, approved=False)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM learning_activities").fetchone()[0], 0)

        activity_id = save_review_proposal(self.root, proposal, approved=True)
        self.assertEqual(save_review_proposal(self.root, proposal, approved=True), activity_id)
        changed = self.review_proposal("attempt-001")
        changed["learner_input"]["learner_response"] = "A different reviewed response"
        with self.assertRaisesRegex(ValueError, "different review payload"):
            save_review_proposal(self.root, changed, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            activities, evidence = conn.execute(
                "SELECT (SELECT COUNT(*) FROM learning_activities), (SELECT COUNT(*) FROM learning_evidence)"
            ).fetchone()
            row = conn.execute("SELECT activity_id, occurred_at FROM learning_activities").fetchone()
        self.assertEqual((activities, evidence), (1, 1))
        self.assertEqual(row[0], activity_id)
        self.assertEqual(row[1], "2026-11-09T12:00:00+00:00")

    def test_review_write_preserves_unknowns_and_all_activity_types(self):
        save_profile_dimension(self.root, self.dimension_proposal(), approved=True)
        activity_types = ("question_attempt", "recall_practice", "reading_observation", "practice_reflection")
        for index, activity_type in enumerate(activity_types):
            with self.subTest(activity_type=activity_type):
                proposal = self.review_proposal(f"type-{index}", activity_type=activity_type)
                if index == 0:
                    proposal.pop("occurred_at")
                    proposal["assistant_analysis"] = "Assistant interpretation stays separate"
                save_review_proposal(self.root, proposal, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            rows = conn.execute(
                "SELECT activity_type, occurred_at, learner_input_json, assistant_analysis FROM learning_activities ORDER BY activity_id"
            ).fetchall()
            dimensions = conn.execute("SELECT COUNT(*) FROM evidence_dimensions").fetchone()[0]
        self.assertEqual([row[0] for row in rows], list(activity_types))
        self.assertIsNone(rows[0][1])
        self.assertEqual(json.loads(rows[0][2])["confidence"], None)
        self.assertEqual(rows[0][3], "Assistant interpretation stays separate")
        self.assertEqual(dimensions, 4)

    def test_review_write_rejects_invalid_payload_and_rolls_back(self):
        invalid_confidence = self.review_proposal("invalid-confidence")
        invalid_confidence["learner_input"]["confidence"] = True
        with self.assertRaisesRegex(ValueError, "learner-reported number"):
            save_review_proposal(self.root, invalid_confidence, approved=True)
        invalid_dimension = self.review_proposal("invalid-dimension")
        invalid_dimension["evidence"][0]["dimensions"][0]["dimension_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "unknown profile dimension"):
            save_review_proposal(self.root, invalid_dimension, approved=True)
        invalid_type = self.review_proposal("invalid-type")
        invalid_type["evidence"][0]["evidence_type"] = "assistant_analysis"
        with self.assertRaisesRegex(ValueError, "evidence_type must be one of"):
            save_review_proposal(self.root, invalid_type, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            activities, evidence = conn.execute(
                "SELECT (SELECT COUNT(*) FROM learning_activities), (SELECT COUNT(*) FROM learning_evidence)"
            ).fetchone()
        self.assertEqual((activities, evidence), (0, 0))

    def test_review_provenance_links_keep_source_locator_and_note_id(self):
        save_profile_dimension(self.root, self.dimension_proposal(), approved=True)
        source = self.root / "01-sources" / "chapter.pdf"
        source.write_bytes(b"review source")
        add_source(self.root, "pdf", "Chapter", str(source), ["biology"])
        note = create_note(self.root, "Derivation note", ["biology"], ["SRC-0001"], ["SRC-0001=page:4"])
        proposal = self.review_proposal(
            "provenance-001",
            sources=[{"source_id": "SRC-0001", "locator": "page:4"}],
            notes=["NOTE-0001"],
        )
        save_review_proposal(self.root, proposal, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            source_link = conn.execute("SELECT source_id, locator FROM evidence_sources").fetchone()
            note_link = conn.execute("SELECT note_id FROM evidence_notes").fetchone()
        self.assertEqual(tuple(source_link), ("SRC-0001", "page:4"))
        self.assertEqual(note_link[0], "NOTE-0001")
        self.assertTrue(note.is_file())
        report = render_profile(self.root, "biology", "2026-11-10T00:00:00Z")
        self.assertIn("SRC-0001 page:4", report)
        self.assertIn("NOTE-0001", report)

    def test_each_evidence_type_is_persisted_as_learner_reviewed_data(self):
        save_profile_dimension(self.root, self.dimension_proposal(minimum=1), approved=True)
        evidence_types = ("learner_statement", "observed_artifact", "verified_outcome")
        for index, evidence_type in enumerate(evidence_types):
            save_review_proposal(
                self.root,
                self.review_proposal(f"evidence-type-{index}", evidence_type=evidence_type),
                approved=True,
            )
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            stored = [row[0] for row in conn.execute("SELECT evidence_type FROM learning_evidence ORDER BY evidence_id")]
        self.assertEqual(stored, list(evidence_types))

    def test_evidence_status_transitions_require_approval_and_keep_history(self):
        save_profile_dimension(self.root, self.dimension_proposal(), approved=True)
        save_review_proposal(self.root, self.review_proposal("status-001", status="pending"), approved=True)
        proposal = {"proposal_version": 1, "evidence_id": "EVD-0001", "status": "conflicting", "reason": "Learner disputes this interpretation"}
        with self.assertRaisesRegex(ValueError, "obtain learner approval"):
            save_evidence_status(self.root, proposal, approved=False)
        save_evidence_status(self.root, proposal, approved=True)
        resolved = {"proposal_version": 1, "evidence_id": "EVD-0001", "status": "confirmed", "reason": "Learner reviewed and confirms the statement"}
        save_evidence_status(self.root, resolved, approved=True)
        supersede = {**resolved, "status": "superseded", "reason": "Learner explicitly replaces this item"}
        save_evidence_status(self.root, supersede, approved=True)
        with self.assertRaisesRegex(ValueError, "terminal"):
            save_evidence_status(self.root, {**resolved, "status": "confirmed"}, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            status = conn.execute("SELECT status FROM learning_evidence WHERE evidence_id = 'EVD-0001'").fetchone()[0]
            history = conn.execute(
                "SELECT from_status, to_status, reason FROM evidence_status_history ORDER BY history_id"
            ).fetchall()
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE evidence_status_history SET reason = 'rewritten'")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM evidence_status_history")
        self.assertEqual(status, "superseded")
        self.assertEqual([tuple(row[:2]) for row in history], [("pending", "conflicting"), ("conflicting", "confirmed"), ("confirmed", "superseded")])

    def test_profile_dimensions_are_approved_topic_scoped_and_empty_by_default(self):
        add_topic(self.root, "chemistry", "Chemistry", None)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM topic_profile_dimensions").fetchone()[0], 0)
        with self.assertRaisesRegex(ValueError, "obtain learner approval"):
            save_profile_dimension(self.root, self.dimension_proposal(), approved=False)
        save_profile_dimension(self.root, self.dimension_proposal(), approved=True)
        invalid = self.dimension_proposal(topic_id="chemistry")
        invalid["minimum_evidence_count"] = True
        with self.assertRaisesRegex(ValueError, "integer from 1 to 1000"):
            save_profile_dimension(self.root, invalid, approved=True)
        invalid_activity = self.dimension_proposal(topic_id="chemistry")
        invalid_activity["eligible_activity_types"] = ["exam_score"]
        with self.assertRaisesRegex(ValueError, "unsupported value"):
            save_profile_dimension(self.root, invalid_activity, approved=True)
        invalid_evidence = self.dimension_proposal(topic_id="chemistry")
        invalid_evidence["eligible_evidence_types"] = ["assistant_analysis"]
        with self.assertRaisesRegex(ValueError, "unsupported value"):
            save_profile_dimension(self.root, invalid_evidence, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            rows = conn.execute("SELECT topic_id, dimension_id FROM topic_profile_dimensions ORDER BY topic_id").fetchall()
        self.assertEqual([tuple(row) for row in rows], [("biology", "derivation")])

    def test_profile_projection_handles_threshold_recency_conflicts_and_no_scores(self):
        save_profile_dimension(self.root, self.dimension_proposal(minimum=2), approved=True)
        as_of = "2026-11-10T00:00:00Z"
        self.assertEqual(project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]["status"], "unknown")
        save_review_proposal(self.root, self.review_proposal("profile-support-1", occurred_at="2026-11-03T00:00:00Z"), approved=True)
        self.assertEqual(project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]["status"], "pending")
        save_review_proposal(self.root, self.review_proposal("profile-support-2", occurred_at="2026-11-09T00:00:00Z"), approved=True)
        dimension = project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]
        self.assertEqual(dimension["status"], "confirmed")
        self.assertEqual(len(dimension["supporting"]), 2)
        self.assertEqual(dimension["evidence_through"], "2026-11-09T00:00:00+00:00")

        save_review_proposal(self.root, self.review_proposal("profile-stale", occurred_at="2026-11-02T00:00:00Z"), approved=True)
        dimension = project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]
        self.assertEqual(dimension["status"], "confirmed")
        self.assertTrue(any(item["recency_state"] == "stale" for item in dimension["evidence"]))

        save_review_proposal(self.root, self.review_proposal("profile-opposing", direction="contradicts"), approved=True)
        dimension = project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]
        self.assertEqual(dimension["status"], "conflicting")
        self.assertEqual((len(dimension["supporting"]), len(dimension["contradicting"])), (2, 1))
        report = render_profile(self.root, "biology", as_of)
        self.assertEqual(report, render_profile(self.root, "biology", as_of))
        self.assertIn("`EVD-0001`", report)
        self.assertIn("`EVD-0004`", report)
        self.assertIn("证据截至：2026-11-09T12:00:00+00:00", report)
        self.assertNotIn("confidence score", report.lower())
        self.assertNotIn("mastery score", report.lower())

        save_evidence_status(self.root, {
            "proposal_version": 1,
            "evidence_id": "EVD-0004",
            "status": "superseded",
            "reason": "Learner reviewed and superseded the disputed direction",
        }, approved=True)
        dimension = project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]
        self.assertEqual(dimension["status"], "confirmed")
        self.assertEqual(dimension["evidence"][-1]["recency_state"], "superseded")

        save_review_proposal(self.root, self.review_proposal("profile-undated", occurred_at=None), approved=True)
        dimension = project_profile(self.root, "biology", as_of)["topics"][0]["dimensions"][0]
        self.assertEqual(dimension["status"], "pending")
        self.assertTrue(any(item["recency_state"] == "undated" for item in dimension["evidence"]))

    def test_profile_report_write_is_atomic_scoped_and_protects_user_files(self):
        report = render_profile(self.root, "biology", "2026-11-10T00:00:00Z")
        output = write_profile_report(self.root, report, "profile.md")
        self.assertTrue(output.is_file())
        self.assertTrue(output.read_text(encoding="utf-8").startswith("<!-- Generated by learnbase profile report; do not edit. -->"))
        write_profile_report(self.root, report.replace("尚未配置", "未配置"), "profile.md")
        self.assertIn("未配置", output.read_text(encoding="utf-8"))
        user_file = self.root / "reports" / "authored.md"
        user_file.write_text("keep this report", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "non-generated report"):
            write_profile_report(self.root, report, "authored.md")
        with self.assertRaisesRegex(ValueError, "inside reports"):
            write_profile_report(self.root, report, "../outside.md")
        self.assertEqual(user_file.read_text(encoding="utf-8"), "keep this report")

    def test_review_and_profile_cli_contracts_run_end_to_end(self):
        cli = Path(__file__).parents[1] / "tools" / "learnbase.py"
        command = [sys.executable, str(cli), "--workspace", str(self.root)]
        dimension = json.dumps(self.dimension_proposal(minimum=1))
        configured = subprocess.run(
            command + ["profile", "dimension", "set", "--proposal", "-", "--approved"],
            input=dimension,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("saved profile dimension", configured.stdout)

        proposal = json.dumps(self.review_proposal("cli-activity"))
        rejected = subprocess.run(
            command + ["review", "add", "--proposal", "-"],
            input=proposal,
            text=True,
            capture_output=True,
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("obtain learner approval", rejected.stderr)
        saved = subprocess.run(
            command + ["review", "add", "--proposal", "-", "--approved"],
            input=proposal,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("recorded activity ACT-0001", saved.stdout)

        transition = json.dumps({
            "proposal_version": 1,
            "evidence_id": "EVD-0001",
            "status": "conflicting",
            "reason": "Learner disputes this evidence item",
        })
        subprocess.run(
            command + ["review", "evidence", "status", "--proposal", "-", "--approved"],
            input=transition,
            text=True,
            capture_output=True,
            check=True,
        )
        shown = subprocess.run(
            command + ["profile", "show", "--topic", "biology", "--as-of", "2026-11-10T00:00:00Z"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("`conflicting`", shown.stdout)
        generated = subprocess.run(
            command + ["profile", "report", "--topic", "biology", "--as-of", "2026-11-10T00:00:00Z", "--output", "cli-profile.md"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("wrote generated profile report cli-profile.md", generated.stdout)
        self.assertIn("`EVD-0001`", (self.root / "reports" / "cli-profile.md").read_text(encoding="utf-8"))

    def test_setup_replaces_init_without_compatibility_alias(self):
        cli = Path(__file__).parents[1] / "tools" / "learnbase.py"
        result = subprocess.run([sys.executable, str(cli), "init"], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_topic_proposal_requires_approval_before_writing(self):
        proposal = {
            "proposal_version": 1,
            "topic_id": "astronomy",
            "name": "Astronomy",
            "learning_goal": "Understand stellar evolution",
        }
        with self.assertRaisesRegex(ValueError, "obtain learner approval"):
            save_topic_proposal(self.root, proposal, approved=False)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            topics = conn.execute("SELECT COUNT(*) FROM topics WHERE topic_id = 'astronomy'").fetchone()[0]
            configs = conn.execute("SELECT COUNT(*) FROM topic_config WHERE topic_id = 'astronomy'").fetchone()[0]
        self.assertEqual((topics, configs), (0, 0))

    def test_approved_topic_proposal_preserves_unknown_and_empty_values(self):
        proposal = {
            "proposal_version": 1,
            "topic_id": "astronomy",
            "name": "Astronomy",
            "parent_id": None,
            "learning_goal": "Understand stellar evolution",
            "prior_background": None,
            "constraints": None,
            "source_hints": [],
            "progress_signals": ["Explain a star lifecycle"],
        }
        save_topic_proposal(self.root, proposal, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            row = conn.execute(
                """SELECT t.name, c.learning_goal, c.prior_background, c.constraints_json,
                          c.source_hints_json, c.progress_signals_json, c.approved_at
                   FROM topics t JOIN topic_config c USING (topic_id)
                   WHERE t.topic_id = 'astronomy'"""
            ).fetchone()
        self.assertEqual(row[:6], (
            "Astronomy",
            "Understand stellar evolution",
            None,
            None,
            "[]",
            '["Explain a star lifecycle"]',
        ))
        self.assertTrue(row[6])

    def test_invalid_topic_proposal_does_not_create_partial_rows(self):
        invalid_parent = {
            "proposal_version": 1,
            "topic_id": "astronomy",
            "name": "Astronomy",
            "parent_id": "missing-parent",
        }
        with self.assertRaisesRegex(ValueError, "unknown parent topic"):
            save_topic_proposal(self.root, invalid_parent, approved=True)
        duplicate = {
            "proposal_version": 1,
            "topic_id": "biology",
            "name": "Duplicate Biology",
        }
        with self.assertRaisesRegex(ValueError, "topic already exists"):
            save_topic_proposal(self.root, duplicate, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            configs = conn.execute("SELECT COUNT(*) FROM topic_config").fetchone()[0]
        self.assertEqual((topics, configs), (1, 0))

    def test_topic_onboard_cli_requires_approval_and_reads_stdin(self):
        cli = Path(__file__).parents[1] / "tools" / "learnbase.py"
        command = [sys.executable, str(cli), "--workspace", str(self.root), "topic", "onboard", "--proposal", "-"]
        payload = json.dumps({
            "proposal_version": 1,
            "topic_id": "astronomy",
            "name": "Astronomy",
            "learning_goal": None,
        })
        rejected = subprocess.run(command, input=payload, text=True, capture_output=True)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("obtain learner approval", rejected.stderr)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM topics WHERE topic_id = 'astronomy'").fetchone()[0], 0)

        accepted = subprocess.run(command + ["--approved"], input=payload, text=True, capture_output=True, check=True)
        self.assertIn("created approved topic astronomy", accepted.stdout)

    def test_invalid_proposal_fields_are_rejected_without_writes(self):
        proposal = {
            "proposal_version": 1,
            "topic_id": "astronomy",
            "name": "Astronomy",
            "unexpected": "value",
        }
        with self.assertRaisesRegex(ValueError, "unknown topic proposal fields"):
            save_topic_proposal(self.root, proposal, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            topics = conn.execute("SELECT COUNT(*) FROM topics WHERE topic_id = 'astronomy'").fetchone()[0]
            configs = conn.execute("SELECT COUNT(*) FROM topic_config WHERE topic_id = 'astronomy'").fetchone()[0]
        self.assertEqual((topics, configs), (0, 0))

    def test_topic_proposal_version_must_be_an_integer(self):
        for version in (1.0, True):
            with self.subTest(version=version):
                proposal = {
                    "proposal_version": version,
                    "topic_id": "astronomy",
                    "name": "Astronomy",
                }
                with self.assertRaisesRegex(ValueError, "proposal_version must be 1"):
                    save_topic_proposal(self.root, proposal, approved=True)
        with closing(sqlite3.connect(self.root / "data" / "learnbase.sqlite3")) as conn:
            topics = conn.execute("SELECT COUNT(*) FROM topics WHERE topic_id = 'astronomy'").fetchone()[0]
            configs = conn.execute("SELECT COUNT(*) FROM topic_config WHERE topic_id = 'astronomy'").fetchone()[0]
        self.assertEqual((topics, configs), (0, 0))

    def test_template_copy_onboarding_does_not_write_into_template_source(self):
        repository = Path(__file__).parents[1]
        source_db = repository / "data" / "learnbase.sqlite3"
        source_snapshot = source_db.read_bytes() if source_db.exists() else None
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "learning-copy"
            shutil.copytree(
                repository,
                workspace,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "data"),
            )
            cli = workspace / "tools" / "learnbase.py"
            setup = subprocess.run(
                [sys.executable, str(cli), "--workspace", str(workspace), "setup"],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("set up", setup.stdout)
            proposal = json.dumps({"proposal_version": 1, "topic_id": "astronomy", "name": "Astronomy"})
            subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "--workspace",
                    str(workspace),
                    "topic",
                    "onboard",
                    "--proposal",
                    "-",
                    "--approved",
                ],
                input=proposal,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue((workspace / "data" / "learnbase.sqlite3").is_file())
        self.assertEqual(source_db.read_bytes() if source_db.exists() else None, source_snapshot)

    def test_fresh_template_cli_replays_source_review_profile_and_card_workflow(self):
        repository = Path(__file__).parents[1]
        template_db = repository / "data/learnbase.sqlite3"
        self.assertFalse(template_db.exists(), "template source must contain no learner database")
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "learner-copy"
            shutil.copytree(repository, workspace, symlinks=True, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "data"))
            cli = workspace / "tools/learnbase.py"

            def run(*args, proposal=None):
                return subprocess.run(
                    [sys.executable, str(cli), "--workspace", str(workspace), *args], cwd=workspace,
                    input=None if proposal is None else json.dumps(proposal), text=True, capture_output=True, check=True,
                ).stdout

            run("setup")
            run("topic", "onboard", "--proposal", "-", "--approved", proposal={"proposal_version": 1, "topic_id": "biology", "name": "Biology"})
            run("source", "add", "web", "--url", "https://example.org/biology", "--title", "Biology", "--topic", "biology")
            note_path = run("note", "new", "--title", "Cell membrane", "--topic", "biology", "--source", "SRC-0001", "--locator", "SRC-0001=section:Membrane").strip().split("created ", 1)[1]
            run("note", "validate", note_path)
            run("profile", "dimension", "set", "--proposal", "-", "--approved", proposal=self.dimension_proposal())
            review = self.review_proposal("fresh-replay", sources=[{"source_id": "SRC-0001", "locator": "section:Membrane"}], notes=["NOTE-0001"])
            run("review", "add", "--proposal", "-", "--approved", proposal=review)
            profile = run("profile", "show", "--topic", "biology")
            self.assertIn("EVD-0001", profile)
            run("card", "draft", "save", "--proposal", "-", "--approved", proposal=self.card_proposal())
            listing = run("card", "draft", "list", "--topic", "biology").strip().split("\t")
            self.assertEqual(listing[:3], ["CARD-0001", "biology", "cell-membrane-function"])
            run("card", "draft", "validate", listing[3])
            self.assertIn("section:Membrane", (workspace / listing[3]).read_text())
            for host in (".claude", ".cursor", ".workbuddy"):
                self.assertEqual((workspace / host / "skills/learnbase-flashcards").resolve(), (workspace / ".agents/skills/learnbase-flashcards").resolve())
        self.assertFalse(template_db.exists())

    def test_onboarding_skill_is_canonical_and_workbuddy_link_resolves(self):
        repository = Path(__file__).parents[1]
        skill = repository / ".agents" / "skills" / "learnbase-onboarding" / "SKILL.md"
        link = repository / ".workbuddy" / "skills" / "learnbase-onboarding"
        self.assertTrue(skill.is_file())
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve() / "SKILL.md", skill.resolve())
        text = skill.read_text(encoding="utf-8")
        self.assertIn("explicit approval", text)
        self.assertIn("null", text)
        self.assertIn("topic onboard --proposal - --approved", text)

    def test_review_skill_is_canonical_and_host_links_resolve(self):
        repository = Path(__file__).parents[1]
        skill = repository / ".agents" / "skills" / "learnbase-review" / "SKILL.md"
        self.assertTrue(skill.is_file())
        for link in (
            repository / ".workbuddy" / "skills" / "learnbase-review",
            repository / ".cursor" / "skills" / "learnbase-review",
            repository / ".claude" / "skills" / "learnbase-review",
        ):
            with self.subTest(link=link):
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.resolve() / "SKILL.md", skill.resolve())
        skill_text = skill.read_text(encoding="utf-8")
        self.assertIn("explicit learner approval", skill_text)
        self.assertIn("assistant_analysis", skill_text)
        self.assertIn("profile dimension set", skill_text)
        self.assertIn("idempotency_key", skill_text)


if __name__ == "__main__":
    unittest.main()
