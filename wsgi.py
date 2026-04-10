import sys

import click
import pytest
from App.controllers import (
    addBox,
    create_loan,
    create_location,
    create_patron,
    create_staff_record,
    create_staff_user,
    create_student_record,
    create_user,
    get_all_loans,
    get_all_locations,
    get_all_patrons,
    get_all_staff_records,
    get_all_staff_users,
    get_all_student_records,
    get_all_users,
    get_all_users_json,
    getAllBoxes,
    initialize,
    return_loan,
)
from App.database import db, get_migrate
from App.main import create_app
from App.models import User
from flask.cli import AppGroup, with_appcontext

app = create_app()
migrate = get_migrate(app)




# -----------------------------------------------------------------------------
# Database initialisation
# -----------------------------------------------------------------------------


@app.cli.command("init", help="Drops, recreates, and seeds the database")
def init():
    initialize()


# -----------------------------------------------------------------------------
# User commands  –  flask user <command>
# -----------------------------------------------------------------------------

user_cli = AppGroup("user", help="User object commands")


@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
def create_user_command(username, password):
    user = create_user(username, password)
    if user:
        print(f"User '{username}' created with id {user.userID}.")
    else:
        print(f"Failed to create user '{username}'.")


@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == "json":
        print(get_all_users_json())
    else:
        for u in get_all_users():
            print(u)


app.cli.add_command(user_cli)


# -----------------------------------------------------------------------------
# Location commands  –  flask location <command>
# -----------------------------------------------------------------------------

location_cli = AppGroup("location", help="Location object commands")


@location_cli.command("create", help="Creates a location")
@click.argument("geo_location")
def create_location_command(geo_location):
    loc = create_location(geo_location)
    if loc:
        print(f"Location '{geo_location}' created with id {loc.locationID}.")
    else:
        print("Failed to create location.")


@location_cli.command("list", help="Lists all locations")
def list_locations_command():
    locations = get_all_locations()
    if not locations:
        print("No locations found.")
    for loc in locations:
        print(loc)


app.cli.add_command(location_cli)


# -----------------------------------------------------------------------------
# Box commands  –  flask box <command>
# -----------------------------------------------------------------------------

box_cli = AppGroup("box", help="Box object commands")


@box_cli.command("create", help="Creates a box")
@click.argument("bay_no", type=int)
@click.argument("row_no", type=int)
@click.argument("column_no", type=int)
@click.argument("location_id", type=int)
@click.option("--barcode", default=None, help="Optional barcode string")
def create_box_command(bay_no, row_no, column_no, location_id, barcode):
    box = addBox(
        bayNo=bay_no,
        rowNo=row_no,
        columnNo=column_no,
        locationID=location_id,
        barcode=barcode,
    )
    if box:
        print(f"Box created with id {box.boxID}.")
    else:
        print("Failed to create box.")


@box_cli.command("list", help="Lists all boxes")
def list_boxes_command():
    boxes = getAllBoxes()
    if not boxes:
        print("No boxes found.")
    for box in boxes:
        print(box)


app.cli.add_command(box_cli)


# -----------------------------------------------------------------------------
# Staff commands  –  flask staff <command>
# -----------------------------------------------------------------------------

staff_cli = AppGroup("staff", help="Staff user commands")


@staff_cli.command("create", help="Creates a staff user from an existing user ID")
@click.argument("username")
@click.argument("password")
def create_staff_command(username, password):
    user = create_user(username, password)
    if not user:
        print(f"Failed to create user '{username}'.")
        return
    staff = create_staff_user(user.userID)
    if staff:
        print(
            f"Staff user created: userID={user.userID}, staffUserID={staff.staffUserID}."
        )
    else:
        print("Failed to create staff profile.")


@staff_cli.command("list", help="Lists all staff users")
def list_staff_command():
    staff_users = get_all_staff_users()
    if not staff_users:
        print("No staff users found.")
    for s in staff_users:
        print(s)


app.cli.add_command(staff_cli)


# -----------------------------------------------------------------------------
# Patron commands  –  flask patron <command>
# -----------------------------------------------------------------------------

patron_cli = AppGroup("patron", help="Patron commands")


@patron_cli.command("create", help="Creates a patron from an existing user ID")
@click.argument("username")
@click.argument("password")
def create_patron_command(username, password):
    user = create_user(username, password)
    if not user:
        print(f"Failed to create user '{username}'.")
        return
    patron = create_patron(user.userID)
    if patron:
        print(f"Patron created: userID={user.userID}, patronID={patron.patronID}.")
    else:
        print("Failed to create patron profile.")


@patron_cli.command("list", help="Lists all patrons")
def list_patrons_command():
    patrons = get_all_patrons()
    if not patrons:
        print("No patrons found.")
    for p in patrons:
        print(p)


app.cli.add_command(patron_cli)


# -----------------------------------------------------------------------------
# Loan commands  –  flask loan <command>
# -----------------------------------------------------------------------------

loan_cli = AppGroup("loan", help="Loan commands")


@loan_cli.command("create", help="Creates a loan for a patron")
@click.argument("patron_id", type=int)
@click.option(
    "--staff-id", type=int, default=None, help="Staff user ID processing the loan"
)
def create_loan_command(patron_id, staff_id):
    loan = create_loan(patronID=patron_id, processedByStaffUserID=staff_id)
    if loan:
        print(f"Loan created with id {loan.loanID} for patron {patron_id}.")
    else:
        print("Failed to create loan.")


@loan_cli.command("return", help="Marks a loan as returned")
@click.argument("loan_id", type=int)
def return_loan_command(loan_id):
    loan = return_loan(loan_id)
    if loan:
        print(f"Loan {loan_id} returned on {loan.returnDate}.")
    else:
        print(f"Loan {loan_id} not found.")


@loan_cli.command("list", help="Lists all loans")
def list_loans_command():
    loans = get_all_loans()
    if not loans:
        print("No loans found.")
    for loan in loans:
        print(loan)


app.cli.add_command(loan_cli)


# -----------------------------------------------------------------------------
# File record commands  –  flask record <command>
# -----------------------------------------------------------------------------

record_cli = AppGroup("record", help="File record commands")


@record_cli.command("student", help="Creates a student record for a file")
@click.argument("file_id", type=int)
@click.argument("certificate_diploma")
@click.argument("code")
def create_student_record_command(file_id, certificate_diploma, code):
    record = create_student_record(
        fileID=file_id, certificateDiploma=certificate_diploma, code=code
    )
    if record:
        print(f"Student record created with id {record.studentID}.")
    else:
        print("Failed to create student record.")


@record_cli.command("staff", help="Creates a staff record for a file")
@click.argument("file_id", type=int)
@click.argument("file_number")
@click.argument("file_title")
@click.option("--post", default=None)
@click.option("--unit", default=None, help="Organisation unit")
@click.option("--notes", default=None)
def create_staff_record_command(file_id, file_number, file_title, post, unit, notes):
    record = create_staff_record(
        fileID=file_id,
        fileNumber=file_number,
        fileTitle=file_title,
        post=post,
        organisationUnit=unit,
        notes=notes,
    )
    if record:
        print(f"Staff record created with id {record.staffRecordID}.")
    else:
        print("Failed to create staff record.")


@record_cli.command("list-students", help="Lists all student records")
def list_student_records_command():
    records = get_all_student_records()
    if not records:
        print("No student records found.")
    for r in records:
        print(r)


@record_cli.command("list-staff", help="Lists all staff records")
def list_staff_records_command():
    records = get_all_staff_records()
    if not records:
        print("No staff records found.")
    for r in records:
        print(r)


app.cli.add_command(record_cli)


# -----------------------------------------------------------------------------
# Test commands  –  flask test <command>
# -----------------------------------------------------------------------------

test = AppGroup("test", help="Testing commands")


@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))


app.cli.add_command(test)
