#!/usr/bin/env python3
"""
Insert a comprehensive 'File Tests' folder into the genCAT Postman collection.

Usage:
    python3 add_file_tests.py

The script:
1. Reads postman_collection.json
2. Updates the collection description to mention 5 folders
3. Adds a 'newFileID' collection variable
4. Inserts the File Tests folder between Box Tests and Integration Test Flow
5. Writes the updated collection back to postman_collection.json
"""

import json
import pathlib

COLLECTION_PATH = pathlib.Path(__file__).parent / "postman_collection.json"


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


def build_file_tests_folder():
    """Build the complete File Tests folder with all test items."""
    items = []

    # ── Setup: Init DB ──────────────────────────────────────────────
    items.append(
        make_test_item(
            "File Setup - Initialize Database",
            "GET",
            ["init"],
            [
                "pm.test('Database initialized', function () {",
                "    pm.response.to.have.status(200);",
                "    pm.expect(pm.response.json().message).to.eql('db initialized!');",
                "});",
            ],
            description="Seeds DB with 11 files across 7 boxes and 4 locations.",
        )
    )

    # ── Setup: Login ────────────────────────────────────────────────
    items.append(
        make_test_item(
            "File Setup - Login",
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
            description="Auth for file tests.",
        )
    )

    # ── GET /api/files - all files ──────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files - Retrieve all files",
            "GET",
            ["api", "files"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Response is an array of 11 files', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(11);",
                "});",
                "",
                "pm.test('Each file has required fields', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f).to.have.all.keys('fileID','boxID','fileType','description','status','dateCreated');",
                "    });",
                "});",
                "",
                "pm.test('Files include both Student and Staff types', function () {",
                "    var types = [...new Set(pm.response.json().map(function (f) { return f.fileType; }))];",
                "    pm.expect(types).to.include('Student');",
                "    pm.expect(types).to.include('Staff');",
                "});",
            ],
            headers=[auth_header()],
            description="Retrieves every file. Seed creates 11.",
        )
    )

    # ── GET /api/files - unauthenticated ────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files - Reject unauthenticated request",
            "GET",
            ["api", "files"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            description="No JWT. Expects 401.",
        )
    )

    # ── GET /files/1 - Student file, Available ──────────────────────
    items.append(
        make_test_item(
            "GET /files/1 - Retrieve file 1 (Student, Available)",
            "GET",
            ["files", "1"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Correct file returned', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileID).to.eql(1);",
                "    pm.expect(j.fileType).to.eql('Student');",
                "    pm.expect(j.status).to.eql('Available');",
                "});",
                "",
                "pm.test('File has all detail fields', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.have.all.keys(",
                "        'fileID','boxID','locationID','loanID','fileType',",
                "        'description','previousDesignation','createdByStaffUserID',",
                "        'dateCreated','status'",
                "    );",
                "});",
                "",
                "pm.test('File 1 is in box 1', function () {",
                "    pm.expect(pm.response.json().boxID).to.eql(1);",
                "});",
                "",
                "pm.test('File 1 description contains transcript', function () {",
                "    pm.expect(pm.response.json().description).to.include('transcript');",
                "});",
            ],
            headers=[auth_header()],
            description="File 1: Student transcript - BSc Computer Science, box 1, Available.",
        )
    )

    # ── GET /files/7 - Staff file, Available ────────────────────────
    items.append(
        make_test_item(
            "GET /files/7 - Retrieve file 7 (Staff, Available)",
            "GET",
            ["files", "7"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Correct file returned', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileID).to.eql(7);",
                "    pm.expect(j.fileType).to.eql('Staff');",
                "    pm.expect(j.status).to.eql('Available');",
                "});",
                "",
                "pm.test('Staff file is in box 7', function () {",
                "    pm.expect(pm.response.json().boxID).to.eql(7);",
                "});",
                "",
                "pm.test('Description mentions personnel file', function () {",
                "    pm.expect(pm.response.json().description.toLowerCase()).to.include('personnel');",
                "});",
            ],
            headers=[auth_header()],
            description="File 7: Staff personnel file - Senior Lecturer, box 7, Available.",
        )
    )

    # ── GET /files/10 - On Loan ─────────────────────────────────────
    items.append(
        make_test_item(
            "GET /files/10 - Retrieve file 10 (On Loan)",
            "GET",
            ["files", "10"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('File 10 is On Loan', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileID).to.eql(10);",
                "    pm.expect(j.status).to.eql('On Loan');",
                "});",
                "",
                "pm.test('File 10 has a loanID set', function () {",
                "    pm.expect(pm.response.json().loanID).to.not.be.null;",
                "});",
                "",
                "pm.test('File 10 is Student type in box 4', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileType).to.eql('Student');",
                "    pm.expect(j.boxID).to.eql(4);",
                "});",
            ],
            headers=[auth_header()],
            description="File 10: Student transcript - BSc Mathematics, box 4, On Loan with active loan.",
        )
    )

    # ── GET /files/11 - second On Loan file ─────────────────────────
    items.append(
        make_test_item(
            "GET /files/11 - Retrieve file 11 (On Loan)",
            "GET",
            ["files", "11"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('File 11 is On Loan', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileID).to.eql(11);",
                "    pm.expect(j.status).to.eql('On Loan');",
                "});",
                "",
                "pm.test('File 11 has a loanID set', function () {",
                "    pm.expect(pm.response.json().loanID).to.not.be.null;",
                "});",
                "",
                "pm.test('File 11 is Student type in box 5', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileType).to.eql('Student');",
                "    pm.expect(j.boxID).to.eql(5);",
                "});",
            ],
            headers=[auth_header()],
            description="File 11: Student transcript - MA History, box 5, On Loan with active loan.",
        )
    )

    # ── GET /files/999 - not found ──────────────────────────────────
    items.append(
        make_test_item(
            "GET /files/999 - File not found",
            "GET",
            ["files", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="Non-existent file. Expects 404.",
        )
    )

    # ── GET /files/1 - unauthenticated ──────────────────────────────
    items.append(
        make_test_item(
            "GET /files/1 - Reject unauthenticated single file request",
            "GET",
            ["files", "1"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            description="No JWT on single file. Expects 401.",
        )
    )

    # ── SEARCH: fileType=Student ────────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?fileType=Student - Search by type",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 8 Student files', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(8);",
                "});",
                "",
                "pm.test('All results are Student type', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f.fileType).to.eql('Student');",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "fileType", "value": "Student"}],
            description="Search files by fileType=Student. Seed has 8 Student files.",
        )
    )

    # ── SEARCH: fileType=Staff ──────────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?fileType=Staff - Search Staff files",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 3 Staff files', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(3);",
                "});",
                "",
                "pm.test('All results are Staff type', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f.fileType).to.eql('Staff');",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "fileType", "value": "Staff"}],
            description="Search files by fileType=Staff. Seed has 3 Staff files.",
        )
    )

    # ── SEARCH: status=Available ────────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?status=Available - Search by status",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 9 Available files', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(9);",
                "});",
                "",
                "pm.test('All results have Available status', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f.status).to.eql('Available');",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "status", "value": "Available"}],
            description="Search files by status=Available. Seed has 9 Available files (11 minus 2 On Loan).",
        )
    )

    # ── SEARCH: status=On Loan ──────────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?status=On Loan - Search On Loan files",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 2 On Loan files', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(2);",
                "});",
                "",
                "pm.test('All results have On Loan status', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f.status).to.eql('On Loan');",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "status", "value": "On Loan"}],
            description="Search files by status=On Loan. Seed has 2 files on active loans.",
        )
    )

    # ── SEARCH: keyword=transcript ──────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?keyword=transcript - Search by keyword",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns files matching keyword transcript', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.be.at.least(5);",
                "});",
                "",
                "pm.test('All results contain transcript in description', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f.description.toLowerCase()).to.include('transcript');",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "keyword", "value": "transcript"}],
            description="Search files by keyword. Several student files have 'transcript' in description.",
        )
    )

    # ── SEARCH: keyword=personnel ───────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?keyword=personnel - Search Staff keyword",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns 3 personnel files', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(3);",
                "});",
                "",
                "pm.test('All results contain personnel in description', function () {",
                "    pm.response.json().forEach(function (f) {",
                "        pm.expect(f.description.toLowerCase()).to.include('personnel');",
                "    });",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "keyword", "value": "personnel"}],
            description="Search files by keyword=personnel. All 3 Staff files have 'Personnel file' in description.",
        )
    )

    # ── SEARCH: keyword with no results ─────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?keyword=NonExistentXYZ - No results",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('No files found message', function () {",
                "    pm.expect(pm.response.json().message).to.include('No files found');",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "keyword", "value": "NonExistentXYZ"}],
            description="Search with a keyword that matches nothing. Expects 404.",
        )
    )

    # ── SEARCH: fileID=1 ────────────────────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?fileID=1 - Search by fileID",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns exactly 1 file', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(1);",
                "});",
                "",
                "pm.test('Returned file has fileID 1', function () {",
                "    pm.expect(pm.response.json()[0].fileID).to.eql(1);",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "fileID", "value": "1"}],
            description="Search files by fileID=1. Should return exactly one result.",
        )
    )

    # ── SEARCH: no filters (returns all) ────────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search - No filters (returns all)",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Returns all 11 files when no filters given', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j).to.be.an('array');",
                "    pm.expect(j.length).to.eql(11);",
                "});",
            ],
            headers=[auth_header()],
            description="Search with no filters should return all files.",
        )
    )

    # ── SEARCH: status=Archived (no results) ────────────────────────
    items.append(
        make_test_item(
            "GET /api/files/search?status=Archived - No archived files",
            "GET",
            ["api", "files", "search"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('No files found message', function () {",
                "    pm.expect(pm.response.json().message).to.include('No files found');",
                "});",
            ],
            headers=[auth_header()],
            query=[{"key": "status", "value": "Archived"}],
            description="No files have Archived status in seed data. Expects 404.",
        )
    )

    # ── POST /files - create new file ───────────────────────────────
    items.append(
        make_test_item(
            "POST /files - Create a new file",
            "POST",
            ["files"],
            [
                "pm.test('Status 201', function () { pm.response.to.have.status(201); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('added successfully');",
                "});",
                "",
                "pm.test('fileID is returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('fileID');",
                "});",
                "",
                "var j = pm.response.json();",
                "if (j.fileID) pm.collectionVariables.set('newFileID', j.fileID.toString());",
            ],
            headers=[json_header(), auth_header()],
            body={
                "boxID": 1,
                "fileType": "Student",
                "description": "Test file - BSc Chemistry",
                "previousDesignation": "T/CH/2024/001",
                "createdByStaffUserID": 1,
            },
            description="Creates a new Student file in box 1.",
        )
    )

    # ── GET /files/{{newFileID}} - verify created file ──────────────
    items.append(
        make_test_item(
            "GET /files/{{newFileID}} - Verify created file",
            "GET",
            ["files", "{{newFileID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('New file has correct fields', function () {",
                "    var j = pm.response.json();",
                "    pm.expect(j.fileType).to.eql('Student');",
                "    pm.expect(j.description).to.eql('Test file - BSc Chemistry');",
                "    pm.expect(j.previousDesignation).to.eql('T/CH/2024/001');",
                "    pm.expect(j.boxID).to.eql(1);",
                "    pm.expect(j.status).to.eql('Available');",
                "});",
            ],
            headers=[auth_header()],
            description="Fetches the newly created file to verify all fields.",
        )
    )

    # ── GET /api/files - verify count is now 12 ─────────────────────
    items.append(
        make_test_item(
            "GET /api/files - Verify file count is now 12",
            "GET",
            ["api", "files"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Total files is now 12', function () {",
                "    pm.expect(pm.response.json().length).to.eql(12);",
                "});",
            ],
            headers=[auth_header()],
            description="Verify count increased to 12 after creating one file.",
        )
    )

    # ── POST /files - missing boxID ─────────────────────────────────
    items.append(
        make_test_item(
            "POST /files - Missing boxID (required field)",
            "POST",
            ["files"],
            [
                "pm.test('Status is 400 or 500 (validation error)', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([400, 500]);",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"fileType": "Student", "description": "Missing boxID test"},
            description="Creates file without boxID. Expects 400 or 500.",
        )
    )

    # ── POST /files - empty body ────────────────────────────────────
    items.append(
        make_test_item(
            "POST /files - Empty request body",
            "POST",
            ["files"],
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

    # ── POST /files - unauthenticated ───────────────────────────────
    items.append(
        make_test_item(
            "POST /files - Reject unauthenticated create",
            "POST",
            ["files"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            headers=[json_header()],
            body={"boxID": 1, "fileType": "Student", "description": "Unauth test"},
            description="No JWT. Expects 401.",
        )
    )

    # ── PUT /files/{{newFileID}} - update file ──────────────────────
    items.append(
        make_test_item(
            "PUT /files/{{newFileID}} - Update file description and type",
            "PUT",
            ["files", "{{newFileID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('updated successfully');",
                "});",
                "",
                "pm.test('fileID matches', function () {",
                "    var expected = parseInt(pm.collectionVariables.get('newFileID'));",
                "    pm.expect(pm.response.json().fileID).to.eql(expected);",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={
                "fileID": "{{newFileID}}",
                "description": "Updated - BSc Chemistry (Honours)",
                "fileType": "Student",
                "previousDesignation": "T/CH/2024/001-UPD",
            },
            description="Updates the description and previousDesignation of the new file.",
        )
    )

    # ── GET /files/{{newFileID}} - verify update ────────────────────
    items.append(
        make_test_item(
            "GET /files/{{newFileID}} - Verify update applied",
            "GET",
            ["files", "{{newFileID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Description was updated', function () {",
                "    pm.expect(pm.response.json().description).to.eql('Updated - BSc Chemistry (Honours)');",
                "});",
                "",
                "pm.test('Previous designation was updated', function () {",
                "    pm.expect(pm.response.json().previousDesignation).to.eql('T/CH/2024/001-UPD');",
                "});",
            ],
            headers=[auth_header()],
            description="Re-fetch to confirm update was applied.",
        )
    )

    # ── PUT /files/999 - not found ──────────────────────────────────
    items.append(
        make_test_item(
            "PUT /files/999 - Update non-existent file",
            "PUT",
            ["files", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"fileID": 999, "description": "Does not exist"},
            description="File 999 does not exist. Expects 404.",
        )
    )

    # ── PUT /files/1 - empty body ───────────────────────────────────
    items.append(
        make_test_item(
            "PUT /files/1 - Empty request body",
            "PUT",
            ["files", "1"],
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

    # ── PUT /files/{{newFileID}}/status - change to Archived ────────
    items.append(
        make_test_item(
            "PUT /files/{{newFileID}}/status - Change status to Archived",
            "PUT",
            ["files", "{{newFileID}}", "status"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('status updated successfully');",
                "});",
                "",
                "pm.test('New status is Archived', function () {",
                "    pm.expect(pm.response.json().status).to.eql('Archived');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"status": "Archived"},
            description="Changes the new file status from Available to Archived.",
        )
    )

    # ── GET /files/{{newFileID}} - verify status change ─────────────
    items.append(
        make_test_item(
            "GET /files/{{newFileID}} - Verify status is Archived",
            "GET",
            ["files", "{{newFileID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('File status is now Archived', function () {",
                "    pm.expect(pm.response.json().status).to.eql('Archived');",
                "});",
            ],
            headers=[auth_header()],
            description="Re-fetch to confirm status changed to Archived.",
        )
    )

    # ── PUT /files/{{newFileID}}/status - change back to Available ──
    items.append(
        make_test_item(
            "PUT /files/{{newFileID}}/status - Change status back to Available",
            "PUT",
            ["files", "{{newFileID}}", "status"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('New status is Available', function () {",
                "    pm.expect(pm.response.json().status).to.eql('Available');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"status": "Available"},
            description="Changes the file status back to Available.",
        )
    )

    # ── PUT /files/999/status - not found ───────────────────────────
    items.append(
        make_test_item(
            "PUT /files/999/status - Status change on non-existent file",
            "PUT",
            ["files", "999", "status"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"status": "Archived"},
            description="File 999 does not exist. Expects 404.",
        )
    )

    # ── PUT /files/1/status - missing status field ──────────────────
    items.append(
        make_test_item(
            "PUT /files/1/status - Missing status field in body",
            "PUT",
            ["files", "1", "status"],
            [
                "pm.test('Status 400', function () { pm.response.to.have.status(400); });",
                "",
                "pm.test('Error indicates status required', function () {",
                "    pm.expect(pm.response.json().error).to.include('required');",
                "});",
            ],
            headers=[json_header(), auth_header()],
            body={"description": "No status field"},
            description="Body without status field. Expects 400.",
        )
    )

    # ── DELETE /files/{{newFileID}} - delete the test file ──────────
    items.append(
        make_test_item(
            "DELETE /files/{{newFileID}} - Delete the test file",
            "DELETE",
            ["files", "{{newFileID}}"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Success message', function () {",
                "    pm.expect(pm.response.json().message).to.include('deleted successfully');",
                "});",
            ],
            headers=[auth_header()],
            description="Deletes the file created earlier.",
        )
    )

    # ── GET /files/{{newFileID}} - verify deleted ───────────────────
    items.append(
        make_test_item(
            "GET /files/{{newFileID}} - Verify file was deleted",
            "GET",
            ["files", "{{newFileID}}"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="Fetch deleted file. Expects 404.",
        )
    )

    # ── GET /api/files - verify count back to 11 ────────────────────
    items.append(
        make_test_item(
            "GET /api/files - Verify file count back to 11",
            "GET",
            ["api", "files"],
            [
                "pm.test('Status 200', function () { pm.response.to.have.status(200); });",
                "",
                "pm.test('Total files is back to 11', function () {",
                "    pm.expect(pm.response.json().length).to.eql(11);",
                "});",
            ],
            headers=[auth_header()],
            description="Confirms 11 files after deletion.",
        )
    )

    # ── DELETE /files/999 - not found ───────────────────────────────
    items.append(
        make_test_item(
            "DELETE /files/999 - Delete non-existent file",
            "DELETE",
            ["files", "999"],
            [
                "pm.test('Status 404', function () { pm.response.to.have.status(404); });",
                "",
                "pm.test('Error message returned', function () {",
                "    pm.expect(pm.response.json()).to.have.property('error');",
                "});",
            ],
            headers=[auth_header()],
            description="File 999 not found. Expects 404.",
        )
    )

    # ── DELETE /files/1 - unauthenticated ───────────────────────────
    items.append(
        make_test_item(
            "DELETE /files/1 - Reject unauthenticated delete",
            "DELETE",
            ["files", "1"],
            [
                "pm.test('Status is 401 or redirect', function () {",
                "    pm.expect(pm.response.code).to.be.oneOf([401, 302, 422]);",
                "});",
            ],
            description="No JWT. Expects 401.",
        )
    )

    return {
        "name": "File Tests",
        "description": (
            "File API test suite covering GET (all, single, not found, search by "
            "type/status/keyword/location), POST (create, validation), PUT (update, "
            "status change), and DELETE endpoints. Seed creates 11 files: 8 Student "
            "and 3 Staff. Files 10-11 are On Loan."
        ),
        "item": items,
    }


def main():
    # 1. Read original collection
    with open(COLLECTION_PATH, "r") as f:
        collection = json.load(f)

    # 2. Update collection description
    collection["info"]["description"] = (
        "Postman test suite for the genCAT Archive & Records Management system.\n\n"
        "Organized into five folders:\n"
        "1. Auth Tests - Validates good/bad login credentials, identity verification, and logout.\n"
        "2. Location Tests - Validates GET and POST location endpoints.\n"
        "3. Box Tests - Validates GET, POST, PUT, and DELETE box endpoints.\n"
        "4. File Tests - Validates GET, POST, PUT, DELETE file endpoints, search with filters, "
        "detail view, and status changes.\n"
        "5. Integration Test Flow - 12-step end-to-end workflow.\n\n"
        "Pre-requisite: The Flask server must be running at {{baseUrl}} (default http://localhost:8080)."
    )

    # 3. Add newFileID collection variable if not already present
    var_keys = [v["key"] for v in collection.get("variable", [])]
    if "newFileID" not in var_keys:
        collection["variable"].append(
            {
                "key": "newFileID",
                "value": "",
                "type": "string",
            }
        )

    # 4. Insert File Tests folder before Integration Test Flow
    file_tests_folder = build_file_tests_folder()
    items = collection["item"]

    # Find the index of "Integration Test Flow"
    integration_idx = None
    for i, folder in enumerate(items):
        if folder.get("name") == "Integration Test Flow":
            integration_idx = i
            break

    if integration_idx is not None:
        items.insert(integration_idx, file_tests_folder)
    else:
        # Fallback: append before last item or at end
        items.append(file_tests_folder)

    # 5. Write back
    with open(COLLECTION_PATH, "w") as f:
        json.dump(collection, f, indent=2)

    print(
        f"✅ File Tests folder inserted with {len(file_tests_folder['item'])} test cases."
    )
    print(f"✅ Collection saved to {COLLECTION_PATH}")


if __name__ == "__main__":
    main()
