"""
Tests for file and loan controllers (unit) and new HTML/API routes (integration).

Run with:
    source venv/bin/activate
    pytest App/tests/test_file_loan.py -v
"""

import logging
import unittest

import pytest

from App.controllers.box import addBox
from App.controllers.file import (
    addFile,
    changeFileStatus,
    deleteFile,
    getAllFiles,
    searchFile,
    updateFile,
    viewFile,
)
from App.controllers.loan import (
    checkout_files,
    create_loan,
    delete_loan,
    get_active_loans,
    get_all_loans,
    get_loan,
    get_loan_files,
    get_returned_loans,
    return_loan,
)
from App.controllers.location import create_location
from App.controllers.patron import create_patron
from App.controllers.staffUser import create_staff_user
from App.controllers.user import create_user
from App.database import create_db, db
from App.main import create_app

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared fixture – one DB per module, JWT cookie auth disabled (use headers)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="module")
def test_app():
    """
    Create a fresh SQLite database for the module, seed minimal data, and
    expose both the app and a logged-in test client.
    """
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///test_file_loan.db",
            # Allow JWT to be sent via Authorization header in tests; disable
            # the cookie-secure flag so the test client can set cookies over HTTP.
            "JWT_COOKIE_SECURE": False,
            "JWT_TOKEN_LOCATION": ["headers", "cookies"],
        }
    )
    create_db()

    with app.app_context():
        _seed_data()

    yield app

    with app.app_context():
        db.drop_all()


def _seed_data():
    """Populate minimal reference data used across all tests."""
    # Users
    _staff_user_obj = create_user("staffuser", "staffpass")
    _patron_user_obj = create_user("patronuser", "patronpass")

    # Profiles
    create_staff_user(_staff_user_obj.userID)
    create_patron(_patron_user_obj.userID)

    # Location + Box (required FK for files)
    loc = create_location("Test Library – Bay Z")
    addBox(
        bayNo=9, rowNo=9, columnNo=9, barcode="BOX-TEST-001", locationID=loc.locationID
    )

    db.session.commit()


# ---------------------------------------------------------------------------
# Helper – obtain a JWT Bearer token for protected route tests
# ---------------------------------------------------------------------------


def _get_token(client, username="staffuser", password="staffpass"):
    """Login via /api/login and return the raw JWT string."""
    resp = client.post(
        "/api/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.get_data(as_text=True)}"
    return resp.get_json()["access_token"]


def _auth_headers(token):
    """Return an Authorization header dict for the given JWT token."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Helper – look up seed objects by attribute
# ---------------------------------------------------------------------------


def _get_box():
    from App.models import Box

    return db.session.scalars(db.select(Box)).first()


def _get_staff_user():
    from App.models import StaffUser

    return db.session.scalars(db.select(StaffUser)).first()


def _get_patron():
    from App.models import Patron

    return db.session.scalars(db.select(Patron)).first()


# ===========================================================================
# FILE CONTROLLER – Unit Tests
# ===========================================================================


class FileControllerUnitTests(unittest.TestCase):
    """Pure controller tests – no HTTP, no JWT."""

    # ------------------------------------------------------------------
    # addFile / viewFile
    # ------------------------------------------------------------------

    def test_add_file_returns_file(self):
        box = _get_box()
        file = addFile(
            boxID=box.boxID,
            fileType="Student",
            description="Unit test file",
            previousDesignation="T/UT/2024/001",
        )
        self.assertIsNotNone(file)
        self.assertEqual(file.fileType, "Student")
        self.assertEqual(file.status, "Available")

    def test_add_file_default_status_is_available(self):
        box = _get_box()
        file = addFile(boxID=box.boxID, fileType="Staff")
        self.assertIsNotNone(file)
        self.assertEqual(file.status, "Available")

    def test_view_file_found(self):
        box = _get_box()
        created = addFile(boxID=box.boxID, fileType="Student", description="view test")
        found = viewFile(created.fileID)
        self.assertIsNotNone(found)
        self.assertEqual(found.fileID, created.fileID)

    def test_view_file_not_found(self):
        result = viewFile(999999)
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # updateFile
    # ------------------------------------------------------------------

    def test_update_file_description(self):
        box = _get_box()
        file = addFile(boxID=box.boxID, fileType="Student", description="original")
        updated = updateFile(fileID=file.fileID, description="updated description")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.description, "updated description")

    def test_update_file_not_found_returns_none(self):
        result = updateFile(fileID=999999, description="ghost")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # changeFileStatus
    # ------------------------------------------------------------------

    def test_change_file_status(self):
        box = _get_box()
        file = addFile(boxID=box.boxID, fileType="Student")
        result = changeFileStatus(file.fileID, "On Loan")
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "On Loan")

    def test_change_file_status_not_found_returns_none(self):
        result = changeFileStatus(999999, "Available")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # getAllFiles / searchFile
    # ------------------------------------------------------------------

    def test_get_all_files_returns_list(self):
        files = getAllFiles()
        self.assertIsInstance(files, list)
        self.assertGreater(len(files), 0)

    def test_search_file_by_type(self):
        box = _get_box()
        addFile(boxID=box.boxID, fileType="Staff", description="search by type")
        results = searchFile(fileType="Staff")
        self.assertIsInstance(results, list)
        self.assertTrue(all(f.fileType == "Staff" for f in results))

    def test_search_file_by_keyword_description(self):
        box = _get_box()
        addFile(
            boxID=box.boxID,
            fileType="Student",
            description="uniqueKeyword2024",
        )
        results = searchFile(keyword="uniqueKeyword2024")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertIn("uniqueKeyword2024", results[0].description)

    def test_search_file_by_keyword_previous_designation(self):
        box = _get_box()
        addFile(
            boxID=box.boxID,
            fileType="Student",
            previousDesignation="DESIG/UNIQUE/9999",
        )
        results = searchFile(keyword="DESIG/UNIQUE/9999")
        self.assertIsInstance(results, list)
        self.assertTrue(
            any("DESIG/UNIQUE/9999" in (f.previousDesignation or "") for f in results)
        )

    def test_search_file_by_status(self):
        box = _get_box()
        f = addFile(boxID=box.boxID, fileType="Student")
        changeFileStatus(f.fileID, "On Loan")
        results = searchFile(status="On Loan")
        self.assertTrue(all(r.status == "On Loan" for r in results))

    def test_search_file_no_match_returns_empty(self):
        results = searchFile(keyword="ZZZNOMATCH99999")
        self.assertEqual(results, [])

    # ------------------------------------------------------------------
    # deleteFile
    # ------------------------------------------------------------------

    def test_delete_file_success(self):
        box = _get_box()
        file = addFile(boxID=box.boxID, fileType="Student", description="to delete")
        fid = file.fileID
        result = deleteFile(fid)
        self.assertTrue(result)
        self.assertIsNone(viewFile(fid))

    def test_delete_file_not_found_returns_false(self):
        result = deleteFile(999999)
        self.assertFalse(result)


# ===========================================================================
# LOAN CONTROLLER – Unit Tests
# ===========================================================================


class LoanControllerUnitTests(unittest.TestCase):
    """Pure controller tests for loan logic."""

    def _make_available_file(self):
        box = _get_box()
        return addFile(boxID=box.boxID, fileType="Student", description="loan file")

    # ------------------------------------------------------------------
    # create_loan
    # ------------------------------------------------------------------

    def test_create_loan_returns_loan(self):
        patron = _get_patron()
        loan = create_loan(patronID=patron.patronID)
        self.assertIsNotNone(loan)
        self.assertEqual(loan.patronID, patron.patronID)
        self.assertIsNone(loan.returnDate)

    def test_create_loan_invalid_patron_returns_none(self):
        loan = create_loan(patronID=999999)
        self.assertIsNone(loan)

    def test_create_loan_with_staff(self):
        patron = _get_patron()
        staff = _get_staff_user()
        loan = create_loan(
            patronID=patron.patronID,
            processedByStaffUserID=staff.staffUserID,
        )
        self.assertIsNotNone(loan)
        self.assertEqual(loan.processedByStaffUserID, staff.staffUserID)

    def test_create_loan_invalid_staff_returns_none(self):
        patron = _get_patron()
        loan = create_loan(patronID=patron.patronID, processedByStaffUserID=999999)
        self.assertIsNone(loan)

    # ------------------------------------------------------------------
    # checkout_files
    # ------------------------------------------------------------------

    def test_checkout_files_sets_status_on_loan(self):
        patron = _get_patron()
        file = self._make_available_file()
        loan = checkout_files(patronID=patron.patronID, file_ids=[file.fileID])
        self.assertIsNotNone(loan)
        refreshed = viewFile(file.fileID)
        self.assertEqual(refreshed.status, "On Loan")
        self.assertEqual(refreshed.loanID, loan.loanID)

    def test_checkout_files_unavailable_file_fails(self):
        patron = _get_patron()
        file = self._make_available_file()
        changeFileStatus(file.fileID, "On Loan")
        loan = checkout_files(patronID=patron.patronID, file_ids=[file.fileID])
        self.assertIsNone(loan)

    def test_checkout_files_nonexistent_file_fails(self):
        patron = _get_patron()
        loan = checkout_files(patronID=patron.patronID, file_ids=[999999])
        self.assertIsNone(loan)

    # ------------------------------------------------------------------
    # get_all_loans / get_active_loans / get_returned_loans
    # ------------------------------------------------------------------

    def test_get_all_loans_returns_list(self):
        loans = get_all_loans()
        self.assertIsInstance(loans, list)

    def test_get_active_loans_all_have_no_return_date(self):
        loans = get_active_loans()
        self.assertTrue(all(loan.returnDate is None for loan in loans))

    def test_get_returned_loans_all_have_return_date(self):
        loans = get_returned_loans()
        self.assertTrue(all(loan.returnDate is not None for loan in loans))

    # ------------------------------------------------------------------
    # get_loan
    # ------------------------------------------------------------------

    def test_get_loan_found(self):
        patron = _get_patron()
        created = create_loan(patronID=patron.patronID)
        found = get_loan(created.loanID)
        self.assertIsNotNone(found)
        self.assertEqual(found.loanID, created.loanID)

    def test_get_loan_not_found_returns_none(self):
        self.assertIsNone(get_loan(999999))

    # ------------------------------------------------------------------
    # return_loan
    # ------------------------------------------------------------------

    def test_return_loan_sets_return_date(self):
        patron = _get_patron()
        file = self._make_available_file()
        loan = checkout_files(patronID=patron.patronID, file_ids=[file.fileID])
        returned = return_loan(loan.loanID)
        self.assertIsNotNone(returned)
        self.assertIsNotNone(returned.returnDate)
        refreshed = viewFile(file.fileID)
        self.assertEqual(refreshed.status, "Available")
        self.assertIsNone(refreshed.loanID)

    def test_return_loan_idempotent(self):
        """Calling return_loan on an already-returned loan should not error."""
        patron = _get_patron()
        loan = create_loan(patronID=patron.patronID)
        return_loan(loan.loanID)
        result = return_loan(loan.loanID)
        self.assertIsNotNone(result)

    def test_return_loan_not_found_returns_none(self):
        result = return_loan(999999)
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # get_loan_files
    # ------------------------------------------------------------------

    def test_get_loan_files_returns_correct_files(self):
        patron = _get_patron()
        f1 = self._make_available_file()
        f2 = self._make_available_file()
        loan = checkout_files(patronID=patron.patronID, file_ids=[f1.fileID, f2.fileID])
        files = get_loan_files(loan.loanID)
        file_ids = {f.fileID for f in files}
        self.assertIn(f1.fileID, file_ids)
        self.assertIn(f2.fileID, file_ids)

    def test_get_loan_files_nonexistent_loan_returns_none(self):
        self.assertIsNone(get_loan_files(999999))

    # ------------------------------------------------------------------
    # delete_loan
    # ------------------------------------------------------------------

    def test_delete_loan_detaches_files(self):
        patron = _get_patron()
        file = self._make_available_file()
        loan = checkout_files(patronID=patron.patronID, file_ids=[file.fileID])
        lid = loan.loanID
        fid = file.fileID
        result = delete_loan(lid)
        self.assertTrue(result)
        self.assertIsNone(get_loan(lid))
        refreshed = viewFile(fid)
        self.assertIsNone(refreshed.loanID)
        self.assertEqual(refreshed.status, "Available")

    def test_delete_loan_not_found_returns_false(self):
        self.assertFalse(delete_loan(999999))


# ===========================================================================
# ROUTE INTEGRATION TESTS – smoke-test all new HTML and API endpoints
# ===========================================================================


@pytest.fixture(scope="module")
def client(test_app):
    """Return a test client with JWT authentication pre-configured."""
    return test_app.test_client()


@pytest.fixture(scope="module")
def auth_token(client):
    """Return a valid Bearer token for staffuser."""
    return _get_token(client)


# ------------------------------------------------------------------
# File HTML pages
# ------------------------------------------------------------------


def test_get_files_page_requires_auth(client):
    """GET /files without auth should return 401."""
    resp = client.get("/files")
    assert resp.status_code == 401


def test_get_files_page_authenticated(client, auth_token):
    """GET /files with valid JWT should render 200 HTML."""
    resp = client.get("/files", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "File Records" in body


def test_get_files_page_keyword_filter(client, auth_token):
    """GET /files?keyword=... should render without error."""
    resp = client.get("/files?keyword=transcript", headers=_auth_headers(auth_token))
    assert resp.status_code == 200


def test_get_files_page_type_filter(client, auth_token):
    resp = client.get("/files?fileType=Student", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Student" in body


def test_get_files_page_status_filter(client, auth_token):
    resp = client.get("/files?status=Available", headers=_auth_headers(auth_token))
    assert resp.status_code == 200


def test_file_detail_page_valid(client, auth_token):
    """GET /files/<id>/detail for an existing file should return 200."""
    # Use the first file in the DB
    files = getAllFiles()
    assert files, "Seed data must include at least one file"
    fid = files[0].fileID
    resp = client.get(f"/files/{fid}/detail", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert str(fid) in body


def test_file_detail_page_not_found(client, auth_token):
    """GET /files/999999/detail should redirect (file not found)."""
    resp = client.get(
        "/files/999999/detail",
        headers=_auth_headers(auth_token),
        follow_redirects=True,
    )
    assert resp.status_code == 200


# ------------------------------------------------------------------
# File API endpoints
# ------------------------------------------------------------------


def test_api_get_all_files(client, auth_token):
    """GET /api/files should return a JSON list."""
    resp = client.get("/api/files", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_api_search_files_no_params(client, auth_token):
    """GET /api/files/search with no params returns all or 404."""
    resp = client.get("/api/files/search", headers=_auth_headers(auth_token))
    assert resp.status_code in (200, 404)


def test_api_search_files_by_type(client, auth_token):
    resp = client.get(
        "/api/files/search?fileType=Student", headers=_auth_headers(auth_token)
    )
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.get_json()
        assert all(f["fileType"] == "Student" for f in data)


def test_api_search_files_by_keyword(client, auth_token):
    resp = client.get(
        "/api/files/search?keyword=unit+test",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code in (200, 404)


def test_api_create_file(client, auth_token):
    """POST /files (JSON) should create a file and return 201."""
    box = _get_box()
    resp = client.post(
        "/files",
        json={
            "boxID": box.boxID,
            "fileType": "Student",
            "description": "API-created file",
            "previousDesignation": "T/API/2024/001",
        },
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "fileID" in data


def test_api_view_single_file(client, auth_token):
    """GET /files/<id> (JSON) should return file data."""
    box = _get_box()
    created = addFile(boxID=box.boxID, fileType="Staff", description="api view test")
    resp = client.get(f"/files/{created.fileID}", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["fileID"] == created.fileID
    assert data["fileType"] == "Staff"


def test_api_view_single_file_not_found(client, auth_token):
    resp = client.get("/files/999999", headers=_auth_headers(auth_token))
    assert resp.status_code == 404


def test_api_update_file(client, auth_token):
    """PUT /files/<id> should update and return 200."""
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student", description="before update")
    resp = client.put(
        f"/files/{file.fileID}",
        json={"fileID": file.fileID, "description": "after update"},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["fileID"] == file.fileID


def test_api_change_file_status(client, auth_token):
    """PUT /files/<id>/status should update status."""
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student")
    resp = client.put(
        f"/files/{file.fileID}/status",
        json={"status": "On Loan"},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "On Loan"


def test_api_change_file_status_missing_body(client, auth_token):
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student")
    resp = client.put(
        f"/files/{file.fileID}/status",
        json={},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 400


def test_api_delete_file(client, auth_token):
    """DELETE /files/<id> should return 200."""
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student", description="to delete via API")
    resp = client.delete(f"/files/{file.fileID}", headers=_auth_headers(auth_token))
    assert resp.status_code == 200


def test_api_delete_file_not_found(client, auth_token):
    resp = client.delete("/files/999999", headers=_auth_headers(auth_token))
    assert resp.status_code == 404


# ------------------------------------------------------------------
# Loan HTML pages
# ------------------------------------------------------------------


def test_get_loans_page_requires_auth(test_app):
    """GET /loans without a JWT should return 401 (uses a fresh cookieless client)."""
    with test_app.test_client() as fresh_client:
        resp = fresh_client.get("/loans")
        assert resp.status_code == 401


def test_get_loans_page_authenticated(client, auth_token):
    """GET /loans with valid JWT should render 200 HTML."""
    resp = client.get("/loans", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Loan Records" in body


def test_get_loans_page_active_filter(client, auth_token):
    resp = client.get("/loans?status=active", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Loan Records" in body


def test_get_loans_page_returned_filter(client, auth_token):
    resp = client.get("/loans?status=returned", headers=_auth_headers(auth_token))
    assert resp.status_code == 200


def test_get_loans_page_patron_filter(client, auth_token):
    patron = _get_patron()
    resp = client.get(
        f"/loans?patronID={patron.patronID}", headers=_auth_headers(auth_token)
    )
    assert resp.status_code == 200


def test_loan_detail_page_valid(client, auth_token):
    """GET /loans/<id>/detail for an existing loan returns 200."""
    patron = _get_patron()
    loan = create_loan(patronID=patron.patronID)
    resp = client.get(f"/loans/{loan.loanID}/detail", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert str(loan.loanID) in body


def test_loan_detail_page_not_found(client, auth_token):
    """GET /loans/999999/detail should redirect to loans list."""
    resp = client.get(
        "/loans/999999/detail",
        headers=_auth_headers(auth_token),
        follow_redirects=True,
    )
    assert resp.status_code == 200


# ------------------------------------------------------------------
# Loan API endpoints
# ------------------------------------------------------------------


def test_api_get_all_loans(client, auth_token):
    """GET /api/loans should return a JSON list."""
    patron = _get_patron()
    create_loan(patronID=patron.patronID)  # ensure at least one exists
    resp = client.get("/api/loans", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_api_get_active_loans(client, auth_token):
    resp = client.get("/api/loans/active", headers=_auth_headers(auth_token))
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.get_json()
        assert all(loan["returnDate"] is None for loan in data)


def test_api_get_returned_loans(client, auth_token):
    # Ensure at least one returned loan exists
    patron = _get_patron()
    loan = create_loan(patronID=patron.patronID)
    return_loan(loan.loanID)

    resp = client.get("/api/loans/returned", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert all(loan["returnDate"] is not None for loan in data)


def test_api_get_single_loan(client, auth_token):
    patron = _get_patron()
    loan = create_loan(patronID=patron.patronID)
    resp = client.get(f"/api/loans/{loan.loanID}", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["loanID"] == loan.loanID


def test_api_get_single_loan_not_found(client, auth_token):
    resp = client.get("/api/loans/999999", headers=_auth_headers(auth_token))
    assert resp.status_code == 404


def test_api_get_loan_files(client, auth_token):
    """GET /api/loans/<id>/files returns files list."""
    patron = _get_patron()
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student", description="api loan file")
    loan = checkout_files(patronID=patron.patronID, file_ids=[file.fileID])
    resp = client.get(
        f"/api/loans/{loan.loanID}/files", headers=_auth_headers(auth_token)
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert any(f["fileID"] == file.fileID for f in data)


def test_api_create_loan(client, auth_token):
    """POST /api/loans should create a loan and return 201."""
    patron = _get_patron()
    resp = client.post(
        "/api/loans",
        json={"patronID": patron.patronID},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "loanID" in data


def test_api_create_loan_missing_patron(client, auth_token):
    resp = client.post(
        "/api/loans",
        json={},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 400


def test_api_create_loan_invalid_patron(client, auth_token):
    resp = client.post(
        "/api/loans",
        json={"patronID": 999999},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 400


def test_api_checkout_files(client, auth_token):
    """POST /api/loans/checkout creates a loan with files."""
    patron = _get_patron()
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student", description="checkout test")
    resp = client.post(
        "/api/loans/checkout",
        json={"patronID": patron.patronID, "fileIDs": [file.fileID]},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "loanID" in data
    assert data["fileCount"] == 1


def test_api_checkout_files_unavailable(client, auth_token):
    """POST /api/loans/checkout with a non-Available file should return 400."""
    patron = _get_patron()
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student", description="unavail checkout")
    changeFileStatus(file.fileID, "On Loan")
    resp = client.post(
        "/api/loans/checkout",
        json={"patronID": patron.patronID, "fileIDs": [file.fileID]},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 400


def test_api_checkout_files_missing_file_ids(client, auth_token):
    patron = _get_patron()
    resp = client.post(
        "/api/loans/checkout",
        json={"patronID": patron.patronID},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 400


def test_api_return_loan(client, auth_token):
    """PUT /api/loans/<id>/return should mark the loan as returned."""
    patron = _get_patron()
    box = _get_box()
    file = addFile(boxID=box.boxID, fileType="Student", description="return via api")
    loan = checkout_files(patronID=patron.patronID, file_ids=[file.fileID])
    resp = client.put(
        f"/api/loans/{loan.loanID}/return",
        json={},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["loanID"] == loan.loanID
    assert data["returnDate"] is not None


def test_api_return_loan_not_found(client, auth_token):
    resp = client.put(
        "/api/loans/999999/return",
        json={},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 404


def test_api_update_loan(client, auth_token):
    """PUT /api/loans/<id> should update mutable loan fields."""
    patron = _get_patron()
    loan = create_loan(patronID=patron.patronID)
    resp = client.put(
        f"/api/loans/{loan.loanID}",
        json={"loanDate": "2025-01-01T00:00:00"},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["loanID"] == loan.loanID


def test_api_update_loan_not_found(client, auth_token):
    resp = client.put(
        "/api/loans/999999",
        json={"loanDate": "2025-01-01T00:00:00"},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 404


def test_api_delete_loan(client, auth_token):
    """DELETE /api/loans/<id> should remove the loan record."""
    patron = _get_patron()
    loan = create_loan(patronID=patron.patronID)
    lid = loan.loanID
    resp = client.delete(
        f"/api/loans/{lid}",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    assert get_loan(lid) is None


def test_api_delete_loan_not_found(client, auth_token):
    resp = client.delete(
        "/api/loans/999999",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 404


def test_api_get_loans_by_patron(client, auth_token):
    """GET /api/loans/patron/<id> should return loans for that patron."""
    patron = _get_patron()
    create_loan(patronID=patron.patronID)
    resp = client.get(
        f"/api/loans/patron/{patron.patronID}",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert all(loan["patronID"] == patron.patronID for loan in data)


def test_api_get_loans_by_patron_not_found(client, auth_token):
    resp = client.get(
        "/api/loans/patron/999999",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 404


# ------------------------------------------------------------------
# Box HTML page
# ------------------------------------------------------------------


def test_get_boxes_page_requires_auth(test_app):
    """GET /boxes without a JWT should return 401 (uses a fresh cookieless client)."""
    with test_app.test_client() as fresh_client:
        resp = fresh_client.get("/boxes")
        assert resp.status_code == 401


def test_get_boxes_page_authenticated(client, auth_token):
    """GET /boxes with valid JWT should render 200 HTML."""
    resp = client.get("/boxes", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Box Records" in body


def test_get_boxes_page_location_filter(client, auth_token):
    """GET /boxes?locationID=<id> should filter by location."""
    from App.models import Location

    loc = db.session.scalars(db.select(Location)).first()
    resp = client.get(
        f"/boxes?locationID={loc.locationID}",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200


def test_get_boxes_page_invalid_location_filter(client, auth_token):
    """GET /boxes?locationID=notanint should fall back to showing all boxes."""
    resp = client.get(
        "/boxes?locationID=notanint",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200


# ------------------------------------------------------------------
# Box API endpoints
# ------------------------------------------------------------------


def test_api_get_all_boxes(client, auth_token):
    resp = client.get("/api/boxes", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_api_get_single_box(client, auth_token):
    box = _get_box()
    resp = client.get(f"/api/boxes/{box.boxID}", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["boxID"] == box.boxID


def test_api_get_single_box_not_found(client, auth_token):
    resp = client.get("/api/boxes/999999", headers=_auth_headers(auth_token))
    assert resp.status_code == 404


def test_api_search_boxes_by_location(client, auth_token):
    from App.models import Location

    loc = db.session.scalars(db.select(Location)).first()
    resp = client.get(
        f"/api/boxes/search?locationID={loc.locationID}",
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code in (200, 404)


def test_api_create_box(client, auth_token):
    """POST /api/boxes should create a box and return 201."""
    from App.models import Location

    loc = db.session.scalars(db.select(Location)).first()
    resp = client.post(
        "/api/boxes",
        json={
            "bayNo": 5,
            "rowNo": 5,
            "columnNo": 5,
            "barcode": "BOX-API-TEST-001",
            "locationID": loc.locationID,
        },
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "box" in data
    assert data["box"]["bayNo"] == 5
