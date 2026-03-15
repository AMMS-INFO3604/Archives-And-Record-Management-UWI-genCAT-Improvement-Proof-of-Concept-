#!/usr/bin/env python3
"""
Insert a comprehensive 'Loan Tests' folder into the genCAT Postman collection.

Usage:
    python3 add_loan_tests.py

The script:
1. Reads postman_collection.json
2. Updates the collection description to mention 6 folders
3. Adds 'newLoanID' and 'checkoutLoanID' collection variables
4. Inserts the Loan Tests folder between File Tests and Integration Test Flow
5. Writes the updated collection back to postman_collection.json

Seed data reminder (5 loans):
  - Loan 1: patron=carol(1), staff=alice(2), RETURNED
  - Loan 2: patron=dave(2),  staff=bob(3),   RETURNED
  - Loan 3: patron=eve(3),   staff=admin(1),  RETURNED
  - Loan 4: patron=frank(4), staff=alice(2), ACTIVE  → file 10 attached
  - Loan 5: patron=grace(5), staff=bob(3),   ACTIVE  → file 11 attached

Patron IDs: carol=1, dave=2, eve=3, frank=4, grace=5
Staff  IDs: admin=1, alice=2, bob=3
"""

import json
import pathlib

COLLECTION_PATH = pathlib.Path(__file__).parent / "postman_collection.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_request(
    method, path_parts, *, headers=None, body=None, description="", query=None
):
    """Build a Postman request object."""
    if headers is None:
        headers = []

    raw_path = "{{baseUrl}}/" + "/".join(path_parts)
    if query:
        raw_path += "?" + "&".join(f"{q['key']}={q['value']}" for q in query)

    url = {
        "raw": raw_path,
        "host": ["{{baseUrl}}"],
        "path": path_parts,
    }
    if query:
        url["query"] = query

    req = {
        "method": method,
        "header": headers,
        "url": url,
        "description": description,
    }
    if body is not None:
        req["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, separators=(",", ":")),
            "options": {"raw": {"language": "json"}},
        }
    return req


def make_test_item(name, method, path_parts, test_lines, **kwargs):
    """Build a complete Postman test item."""
    return {
        "name": name,
        "event": [
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": test_lines,
                },
            }
        ],
        "request": make_request(method, path_parts, **kwargs),
    }


def auth_header():
    return {"key": "Authorization", "value": "Bearer {{jwt_token}}"}


def json_header():
    return {"key": "Content-Type", "value": "application/json"}


# ---------------------------------------------------------------------------
# Loan Tests folder builder
# ---------------------------------------------------------------------------


def build_loan_tests_folder():
    """Build the complete Loan Tests folder with all test items."""
    items = []

    # ══════════════════════════════════════════════════════════════════
    # SETUP
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "Loan Setup - Initialize Database",
            "GET",
            ["init"],
            [
                "pm.test('Database initialized', function () {",
                "    pm.response.to.have.status(200);",
                "    pm.expect(pm.response.json().message).to.eql('db initialized!');",
                "});",
            ],
            description="Seeds DB with 5 loans (3 returned, 2 active), 11 files, 5 patrons, 3 staff.",
        )
    )

    items.append(
        make_test_item(
            "Loan Setup - Login",
            "POST",
            ["api", "login"],
            [
                "pm.test('Login successful', function () {",
                "    pm.response.to.have.status(200);",
                "    pm.expect(pm.response.json()).to.have.property('access_token');",
                "});",
                "var j = pm.response.json();",
                "if (j.access_token) pm.collectionVariables.set('jwt_token', j.access_token);",
            ],
            headers=[json_header()],
            body={"username": "admin", "password": "adminpass"},
            description="Auth for loan tests.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # GET ALL LOANS
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "GET /api/loans - Retrieve all loans",
            "GET",
            ["api", "loans"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Response is an array of 5 loans', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(5);",
                "});",
                "",
                "pm.test('Each loan has required fields', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l).to.have.all.keys(",
                "            'loanID','loanDate','returnDate',",
                "            'processedByStaffUserID','patronID','fileCount'",
                "        );",
                "    });",
                "});",
                "",
                "pm.test('Mix of active and returned loans', function () {",
                "    var active = pm.response.json().filter(function (l) { return l.returnDate === null; });",
                "    var returned = pm.response.json().filter(function (l) { return l.returnDate !== null; });",
                "    pm.expect(active.length).to.eql(2);",
                "    pm.expect(returned.length).to.eql(3);",
                "});",
            ],
            headers=[auth_header()],
            description="Retrieves every loan. Seed creates 5 (3 returned, 2 active).",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans - Reject unauthenticated request",
            "GET",
            ["api", "loans"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            description="No JWT. Expects 401.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # GET ACTIVE / RETURNED
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "GET /api/loans/active - Retrieve active loans",
            "GET",
            ["api", "loans", "active"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 2 active loans', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(2);",
                "});",
                "",
                "pm.test('All active loans have null returnDate', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.returnDate).to.be.null;",
                "    });",
                "});",
                "",
                "pm.test('Active loans have files attached', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.fileCount).to.be.at.least(1);",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            description="Retrieves active (unreturned) loans. Seed has 2.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/returned - Retrieve returned loans",
            "GET",
            ["api", "loans", "returned"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 3 returned loans', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(3);",
                "});",
                "",
                "pm.test('All returned loans have a returnDate', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.returnDate).to.not.be.null;",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            description="Retrieves returned loans. Seed has 3.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # GET SINGLE LOAN
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "GET /api/loans/1 - Retrieve returned loan 1",
            "GET",
            ["api", "loans", "1"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Correct loan returned', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.loanID).to.eql(1);",
                "    pm.expect(j.patronID).to.eql(1);",
                "    pm.expect(j.processedByStaffUserID).to.eql(2);",
                "});",
                "",
                "pm.test('Loan 1 has been returned', function () {",
                "    pm.expect(pm.response.json().returnDate).to.not.be.null;",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 1: patron=carol(1), staff=alice(2), returned.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/4 - Retrieve active loan 4",
            "GET",
            ["api", "loans", "4"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Correct loan returned', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.loanID).to.eql(4);",
                "    pm.expect(j.patronID).to.eql(4);",
                "    pm.expect(j.processedByStaffUserID).to.eql(2);",
                "});",
                "",
                "pm.test('Loan 4 is still active (no returnDate)', function () {",
                "    pm.expect(pm.response.json().returnDate).to.be.null;",
                "});",
                "",
                "pm.test('Loan 4 has 1 file attached', function () {",
                "    pm.expect(pm.response.json().fileCount).to.eql(1);",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 4: patron=frank(4), staff=alice(2), active with file 10.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/5 - Retrieve active loan 5",
            "GET",
            ["api", "loans", "5"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Correct loan returned', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.loanID).to.eql(5);",
                "    pm.expect(j.patronID).to.eql(5);",
                "    pm.expect(j.processedByStaffUserID).to.eql(3);",
                "});",
                "",
                "pm.test('Loan 5 is still active', function () {",
                "    pm.expect(pm.response.json().returnDate).to.be.null;",
                "});",
                "",
                "pm.test('Loan 5 has 1 file attached', function () {",
                "    pm.expect(pm.response.json().fileCount).to.eql(1);",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 5: patron=grace(5), staff=bob(3), active with file 11.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/999 - Loan not found",
            "GET",
            ["api", "loans", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="Non-existent loan. Expects 404.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # GET LOAN FILES
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "GET /api/loans/4/files - Files on active loan 4",
            "GET",
            ["api", "loans", "4", "files"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns array with 1 file', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(1);",
                "});",
                "",
                "pm.test('Attached file is file 10 (BSc Mathematics)', function () {",
                "    var f = pm.response.json()[0];",
                "    pm.expect(f.fileID).to.eql(10);",
                "    pm.expect(f.fileType).to.eql('Student');",
                "    pm.expect(f.status).to.eql('On Loan');",
                "    pm.expect(f.description).to.include('Mathematics');",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 4 has file 10 (BSc Mathematics) attached.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/5/files - Files on active loan 5",
            "GET",
            ["api", "loans", "5", "files"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns array with 1 file', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(1);",
                "});",
                "",
                "pm.test('Attached file is file 11 (MA History)', function () {",
                "    var f = pm.response.json()[0];",
                "    pm.expect(f.fileID).to.eql(11);",
                "    pm.expect(f.fileType).to.eql('Student');",
                "    pm.expect(f.status).to.eql('On Loan');",
                "    pm.expect(f.description).to.include('History');",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 5 has file 11 (MA History) attached.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/1/files - Files on returned loan 1 (empty)",
            "GET",
            ["api", "loans", "1", "files"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Response indicates no files attached', function () {",
                "    var j = pm.response.json();",
                "    // Returned loans have files detached; expect empty array or message",
                "    if (Array.isArray(j)) {",
                "        pm.expect(j.length).to.eql(0);",
                "    } else {",
                "        pm.expect(j.message).to.include('No files');",
                "    }",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 1 is returned; files were detached. Expects empty result.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/999/files - Files on non-existent loan",
            "GET",
            ["api", "loans", "999", "files"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 999 not found. Expects 404.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # GET BY PATRON
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "GET /api/loans/patron/4 - Loans for patron frank",
            "GET",
            ["api", "loans", "patron", "4"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 1 loan for frank', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(1);",
                "});",
                "",
                "pm.test('All loans belong to patron 4', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.patronID).to.eql(4);",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            description="Frank (patron 4) has 1 active loan.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/patron/1 - Loans for patron carol",
            "GET",
            ["api", "loans", "patron", "1"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 1 loan for carol', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(1);",
                "});",
                "",
                "pm.test('Loan is returned', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.returnDate).to.not.be.null;",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            description="Carol (patron 1) has 1 returned loan.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/patron/999 - Loans for non-existent patron",
            "GET",
            ["api", "loans", "patron", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('No loans found message', function () {",
                "    pm.expect(pm.response.json().message).to.include('No loans found');",
                "});",
            ],
            headers=[auth_header()],
            description="Patron 999 does not exist. Expects 404.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # GET BY STAFF
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "GET /api/loans/staff/2 - Loans processed by alice",
            "GET",
            ["api", "loans", "staff", "2"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 2 loans processed by alice', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(2);",
                "});",
                "",
                "pm.test('All loans processed by staff 2', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.processedByStaffUserID).to.eql(2);",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            description="Alice (staff 2) processed loans 1 and 4.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/staff/3 - Loans processed by bob",
            "GET",
            ["api", "loans", "staff", "3"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 2 loans processed by bob', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(2);",
                "});",
                "",
                "pm.test('All loans processed by staff 3', function () {",
                "    pm.response.json().forEach(function (l) {",
                "        pm.expect(l.processedByStaffUserID).to.eql(3);",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            description="Bob (staff 3) processed loans 2 and 5.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/staff/1 - Loans processed by admin",
            "GET",
            ["api", "loans", "staff", "1"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 1 loan processed by admin', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(1);",
                "});",
            ],
            headers=[auth_header()],
            description="Admin (staff 1) processed loan 3.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/staff/999 - Loans for non-existent staff",
            "GET",
            ["api", "loans", "staff", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('No loans found message', function () {",
                "    pm.expect(pm.response.json().message).to.include('No loans found');",
                "});",
            ],
            headers=[auth_header()],
            description="Staff 999 does not exist. Expects 404.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # POST – CREATE BARE LOAN
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "POST /api/loans - Create a bare loan",
            "POST",
            ["api", "loans"],
            [
                "pm.test('Status 201', function () { pm.response.to.have.status(201); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('created successfully');",
                "});",
                "",
                "pm.test('loanID is returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('loanID');",
                "});",
                "",
                "var j = pm.response.json();",
                "if (j.loanID) pm.collectionVariables.set('newLoanID', j.loanID.toString());",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 1, "processedByStaffUserID": 1},
            description="Creates a bare loan for patron carol(1), processed by admin(1).",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/{{newLoanID}} - Verify created loan",
            "GET",
            ["api", "loans", "{{newLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Loan has correct patron and staff', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.patronID).to.eql(1);",
                "    pm.expect(j.processedByStaffUserID).to.eql(1);",
                "});",
                "",
                "pm.test('Loan is active (not returned)', function () {",
                "    pm.expect(pm.response.json().returnDate).to.be.null;",
                "});",
                "",
                "pm.test('No files attached to bare loan', function () {",
                "    pm.expect(pm.response.json().fileCount).to.eql(0);",
                "});",
            ],
            headers=[auth_header()],
            description="Fetches the newly created bare loan to verify fields.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans - Verify loan count is now 6",
            "GET",
            ["api", "loans"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Total loans is now 6', function () {",
                "    pm.expect(pm.response.json().length).to.eql(6);",
                "});",
            ],
            headers=[auth_header()],
            description="Verify count increased to 6 after creating one loan.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans - Missing patronID",
            "POST",
            ["api", "loans"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error mentions patronID', function () {",
                "    pm.expect(pm.response.json().error).to.include('patronID');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"processedByStaffUserID": 1},
            description="Creates loan without patronID. Expects 400.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans - Empty request body",
            "POST",
            ["api", "loans"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            description="No JSON body. Expects 400.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans - Invalid patronID",
            "POST",
            ["api", "loans"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 9999},
            description="Patron 9999 does not exist. Expects 400.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans - Reject unauthenticated create",
            "POST",
            ["api", "loans"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            headers=[json_header()],
            body={"patronID": 1},
            description="No JWT. Expects 401.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # POST – CHECKOUT FILES
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "POST /api/loans/checkout - Checkout file 1 to carol",
            "POST",
            ["api", "loans", "checkout"],
            [
                "pm.test('Status 201', function () { pm.response.to.have.status(201); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('checked out successfully');",
                "});",
                "",
                "pm.test('loanID returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('loanID');",
                "});",
                "",
                "pm.test('fileCount is 1', function () {",
                "    pm.expect(pm.response.json().fileCount).to.eql(1);",
                "});",
                "",
                "var j = pm.response.json();",
                "if (j.loanID) pm.collectionVariables.set('checkoutLoanID', j.loanID.toString());",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 1, "fileIDs": [1], "processedByStaffUserID": 1},
            description="Checks out file 1 (Available) to carol. Creates loan + attaches file.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/{{checkoutLoanID}} - Verify checkout loan",
            "GET",
            ["api", "loans", "{{checkoutLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Loan has 1 file attached', function () {",
                "    pm.expect(pm.response.json().fileCount).to.eql(1);",
                "});",
                "",
                "pm.test('Loan is active', function () {",
                "    pm.expect(pm.response.json().returnDate).to.be.null;",
                "});",
                "",
                "pm.test('Loan patron is carol (1)', function () {",
                "    pm.expect(pm.response.json().patronID).to.eql(1);",
                "});",
            ],
            headers=[auth_header()],
            description="Verify the checkout loan has 1 file and is active.",
        )
    )

    items.append(
        make_test_item(
            "GET /files/1 - Verify file 1 is now On Loan",
            "GET",
            ["files", "1"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('File 1 status is On Loan', function () {",
                "    pm.expect(pm.response.json().status).to.eql('On Loan');",
                "});",
                "",
                "pm.test('File 1 loanID matches checkout loan', function () {",
                "    var expected = parseInt(pm.collectionVariables.get('checkoutLoanID'));",
                "    pm.expect(pm.response.json().loanID).to.eql(expected);",
                "});",
            ],
            headers=[auth_header()],
            description="After checkout, file 1 should be On Loan with loanID set.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans/checkout - Missing fileIDs",
            "POST",
            ["api", "loans", "checkout"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error mentions fileIDs', function () {",
                "    pm.expect(pm.response.json().error).to.include('fileIDs');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 1},
            description="Checkout without fileIDs. Expects 400.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans/checkout - Missing patronID",
            "POST",
            ["api", "loans", "checkout"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error mentions patronID', function () {",
                "    pm.expect(pm.response.json().error).to.include('patronID');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"fileIDs": [2]},
            description="Checkout without patronID. Expects 400.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans/checkout - File already On Loan",
            "POST",
            ["api", "loans", "checkout"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 2, "fileIDs": [1]},
            description="File 1 is already On Loan from previous checkout. Expects 400.",
        )
    )

    items.append(
        make_test_item(
            "POST /api/loans/checkout - Empty request body",
            "POST",
            ["api", "loans", "checkout"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            description="No JSON body on checkout. Expects 400.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # PUT – RETURN LOAN
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "PUT /api/loans/{{checkoutLoanID}}/return - Return the checkout loan",
            "PUT",
            ["api", "loans", "{{checkoutLoanID}}", "return"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('returned successfully');",
                "});",
                "",
                "pm.test('returnDate is set', function () {",
                "    pm.expect(pm.response.json().returnDate).to.not.be.null;",
                "});",
                "",
                "pm.test('loanID matches', function () {",
                "    var expected = parseInt(pm.collectionVariables.get('checkoutLoanID'));",
                "    pm.expect(pm.response.json().loanID).to.eql(expected);",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={},
            description="Returns the checkout loan. Files should revert to Available.",
        )
    )

    items.append(
        make_test_item(
            "GET /files/1 - Verify file 1 is Available after return",
            "GET",
            ["files", "1"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('File 1 status is back to Available', function () {",
                "    pm.expect(pm.response.json().status).to.eql('Available');",
                "});",
                "",
                "pm.test('File 1 loanID is cleared', function () {",
                "    pm.expect(pm.response.json().loanID).to.be.null;",
                "});",
            ],
            headers=[auth_header()],
            description="After returning the loan, file 1 should be Available with loanID null.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/{{checkoutLoanID}} - Verify loan is now returned",
            "GET",
            ["api", "loans", "{{checkoutLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('returnDate is set', function () {",
                "    pm.expect(pm.response.json().returnDate).to.not.be.null;",
                "});",
                "",
                "pm.test('File count is 0 after return', function () {",
                "    pm.expect(pm.response.json().fileCount).to.eql(0);",
                "});",
            ],
            headers=[auth_header()],
            description="Re-fetch checkout loan to confirm it is returned and files detached.",
        )
    )

    items.append(
        make_test_item(
            "PUT /api/loans/999/return - Return non-existent loan",
            "PUT",
            ["api", "loans", "999", "return"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={},
            description="Loan 999 does not exist. Expects 404.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # PUT – UPDATE LOAN
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "PUT /api/loans/{{newLoanID}} - Update loan patron and staff",
            "PUT",
            ["api", "loans", "{{newLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('updated successfully');",
                "});",
                "",
                "pm.test('loanID matches', function () {",
                "    var expected = parseInt(pm.collectionVariables.get('newLoanID'));",
                "    pm.expect(pm.response.json().loanID).to.eql(expected);",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 2, "processedByStaffUserID": 3},
            description="Changes patron from carol(1) to dave(2) and staff from admin(1) to bob(3).",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/{{newLoanID}} - Verify update applied",
            "GET",
            ["api", "loans", "{{newLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Patron updated to dave (2)', function () {",
                "    pm.expect(pm.response.json().patronID).to.eql(2);",
                "});",
                "",
                "pm.test('Staff updated to bob (3)', function () {",
                "    pm.expect(pm.response.json().processedByStaffUserID).to.eql(3);",
                "});",
            ],
            headers=[auth_header()],
            description="Re-fetch to confirm patron and staff were updated.",
        )
    )

    items.append(
        make_test_item(
            "PUT /api/loans/999 - Update non-existent loan",
            "PUT",
            ["api", "loans", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"patronID": 1},
            description="Loan 999 does not exist. Expects 404.",
        )
    )

    items.append(
        make_test_item(
            "PUT /api/loans/1 - Empty request body",
            "PUT",
            ["api", "loans", "1"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            description="No JSON body on update. Expects 400.",
        )
    )

    # ══════════════════════════════════════════════════════════════════
    # DELETE
    # ══════════════════════════════════════════════════════════════════

    items.append(
        make_test_item(
            "DELETE /api/loans/{{newLoanID}} - Delete the bare loan",
            "DELETE",
            ["api", "loans", "{{newLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('deleted successfully');",
                "});",
            ],
            headers=[auth_header()],
            description="Deletes the bare loan created earlier.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans/{{newLoanID}} - Verify bare loan deleted",
            "GET",
            ["api", "loans", "{{newLoanID}}"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="Fetch deleted loan. Expects 404.",
        )
    )

    items.append(
        make_test_item(
            "DELETE /api/loans/{{checkoutLoanID}} - Delete the checkout loan",
            "DELETE",
            ["api", "loans", "{{checkoutLoanID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('deleted successfully');",
                "});",
            ],
            headers=[auth_header()],
            description="Deletes the returned checkout loan.",
        )
    )

    items.append(
        make_test_item(
            "GET /api/loans - Verify loan count back to 5",
            "GET",
            ["api", "loans"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Total loans is back to 5', function () {",
                "    pm.expect(pm.response.json().length).to.eql(5);",
                "});",
            ],
            headers=[auth_header()],
            description="Confirms 5 loans after deleting both test loans.",
        )
    )

    items.append(
        make_test_item(
            "DELETE /api/loans/999 - Delete non-existent loan",
            "DELETE",
            ["api", "loans", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="Loan 999 not found. Expects 404.",
        )
    )

    items.append(
        make_test_item(
            "DELETE /api/loans/1 - Reject unauthenticated delete",
            "DELETE",
            ["api", "loans", "1"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            description="No JWT. Expects 401.",
        )
    )

    return {
        "name": "Loan Tests",
        "description": (
            "Loan API test suite covering GET (all, active, returned, single, "
            "by patron, by staff, loan files), POST (create bare loan, checkout "
            "files, validation errors), PUT (return loan, update loan), and DELETE "
            "endpoints. Seed creates 5 loans: 3 returned, 2 active with files attached."
        ),
        "item": items,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    # 1. Read original collection
    with open(COLLECTION_PATH, "r") as f:
        collection = json.load(f)

    # 2. Update collection description
    collection["info"]["description"] = (
        "Postman test suite for the genCAT Archive & Records Management system.\n\n"
        "Organized into six folders:\n"
        "1. Auth Tests - Validates good/bad login credentials, identity verification, and logout.\n"
        "2. Location Tests - Validates GET and POST location endpoints.\n"
        "3. Box Tests - Validates GET, POST, PUT, and DELETE box endpoints.\n"
        "4. File Tests - Validates GET, POST, PUT, DELETE file endpoints, search with filters, "
        "detail view, and status changes.\n"
        "5. Loan Tests - Validates GET, POST, PUT, DELETE loan endpoints, checkout/return workflows, "
        "and queries by patron/staff.\n"
        "6. Integration Test Flow - 12-step end-to-end workflow.\n\n"
        "Pre-requisite: The Flask server must be running at {{baseUrl}} (default http://localhost:8080)."
    )

    # 3. Add new collection variables if not already present
    var_keys = [v["key"] for v in collection.get("variable", [])]
    for key in ("newLoanID", "checkoutLoanID"):
        if key not in var_keys:
            collection["variable"].append({"key": key, "value": "", "type": "string"})

    # 4. Insert Loan Tests folder before Integration Test Flow
    loan_tests_folder = build_loan_tests_folder()
    items = collection["item"]

    integration_idx = None
    for i, folder in enumerate(items):
        if folder.get("name") == "Integration Test Flow":
            integration_idx = i
            break

    if integration_idx is not None:
        items.insert(integration_idx, loan_tests_folder)
    else:
        items.append(loan_tests_folder)

    # 5. Write back
    with open(COLLECTION_PATH, "w") as f:
        json.dump(collection, f, indent=2)

    print(
        f"Done! Loan Tests folder inserted with {len(loan_tests_folder['item'])} test cases."
    )
    print(f"Collection saved to {COLLECTION_PATH}")


if __name__ == "__main__":
    main()
