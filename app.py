
import os
from datetime import date

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
import mysql.connector
from mysql.connector import Error
from flask_mail import Mail, Message


# -----------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------------------

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "change-this-for-local-development"
)


# -----------------------------------------
# GMAIL EMAIL CONFIGURATION
# -----------------------------------------

app.config["MAIL_SERVER"] = os.getenv(
    "MAIL_SERVER", "smtp.gmail.com"
)

app.config["MAIL_PORT"] = int(
    os.getenv("MAIL_PORT", "587")
)

app.config["MAIL_USE_TLS"] = (
    os.getenv("MAIL_USE_TLS", "True").strip().lower() == "true"
)

app.config["MAIL_USE_SSL"] = (
    os.getenv("MAIL_USE_SSL", "False").strip().lower() == "true"
)

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")

app.config["MAIL_PASSWORD"] = (
    os.getenv("MAIL_PASSWORD", "ootnjdmpxzytrkud").replace(" ", "")
)

app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

# Initialize Flask-Mail AFTER setting the configuration.
mail = Mail(app)

BOOKING_RECEIVER = os.getenv(
    "BOOKING_RECEIVER",
    "vamsibadarala1433@gmail.com"
)


# -----------------------------------------
# MYSQL DATABASE CONNECTION
# -----------------------------------------

def get_db_connection():
    """Connect to the Hanuman Travels database."""

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "hanuman_travels"),
    )


# -----------------------------------------
# SEND BOOKING NOTIFICATION EMAIL
# -----------------------------------------

def send_booking_email(
    booking_id,
    name,
    phone,
    email,
    pickup,
    destination,
    travel_date,
    trip_type,
    car_type,
    passengers,
    requirements,
):
    """Send a booking notification to the business email."""

    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        app.logger.error(
            "Email not sent: Gmail username or app password is missing."
        )
        return False

    if not BOOKING_RECEIVER:
        app.logger.error(
            "Email not sent: BOOKING_RECEIVER is missing."
        )
        return False

    message = Message(
        subject=f"New Car Booking #{booking_id} - Hanuman Travels",
        recipients=[BOOKING_RECEIVER],
        body=f"""
HANUMAN TRAVELS
New Customer Booking Received
========================================

Booking ID: {booking_id}

CUSTOMER DETAILS
Customer Name: {name}
Phone Number: {phone}
Customer Email: {email or 'Not provided'}

TRAVEL DETAILS
Pickup Location: {pickup or 'Not provided'}
Destination: {destination}
Travel Date: {travel_date or 'Not specified'}
Trip Type: {trip_type}
Car Selected: {car_type}
Number of Passengers: {passengers}

ADDITIONAL REQUIREMENTS
{requirements or 'None'}

========================================
This is an automatic notification from
your Hanuman Travels website.
""",
    )

    try:
        mail.send(message)

        app.logger.info(
            "Booking email sent successfully for booking ID %s",
            booking_id,
        )
        return True

    except Exception:
        app.logger.exception(
            "Failed to send booking email for booking ID %s",
            booking_id,
        )
        return False


# -----------------------------------------
# HOME PAGE
# -----------------------------------------

@app.route("/")
def home():
    return render_template(
        "index.html",
        today=date.today().isoformat(),
    )


# -----------------------------------------
# SUBMIT BOOKING
# -----------------------------------------

@app.route("/submit-booking", methods=["POST"])
def submit_booking():

    # Read submitted form values.
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip() or None
    pickup = request.form.get("pickup", "").strip() or None
    destination = request.form.get("destination", "").strip()
    travel_date = request.form.get("travel_date", "").strip() or None
    trip_type = request.form.get("trip_type", "Local").strip()
    car_type = request.form.get("car_type", "Baleno").strip()
    requirements = (
        request.form.get("requirements", "").strip() or None
    )

    try:
        passengers = int(request.form.get("passengers", "1"))
    except (ValueError, TypeError):
        passengers = 0

    # Validate required fields.
    if not name or not phone or not destination:
        flash(
            "Please fill in your name, phone number and destination.",
            "error",
        )
        return redirect(url_for("home") + "#booking")

    if passengers < 1 or passengers > 8:
        flash(
            "Please enter between 1 and 8 passengers.",
            "error",
        )
        return redirect(url_for("home") + "#booking")

    connection = None
    cursor = None

    # -------------------------------------
    # SAVE BOOKING TO MYSQL
    # -------------------------------------

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO customer_bookings
            (
                customer_name,
                phone,
                email,
                pickup,
                destination,
                travel_date,
                trip_type,
                car_type,
                passengers,
                requirements
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            phone,
            email,
            pickup,
            destination,
            travel_date,
            trip_type,
            car_type,
            passengers,
            requirements,
        )

        cursor.execute(sql, values)

        # Get the new booking ID and save the transaction.
        booking_id = cursor.lastrowid
        connection.commit()

        app.logger.info(
            "Booking #%s saved successfully.",
            booking_id,
        )

    except Error:
        app.logger.exception(
            "Database error while saving the booking."
        )

        if connection is not None and connection.is_connected():
            connection.rollback()

        flash(
            "We couldn't save your enquiry. Please try again.",
            "error",
        )
        return redirect(url_for("home") + "#booking")

    except Exception:
        app.logger.exception(
            "Unexpected error while saving the booking."
        )

        if connection is not None and connection.is_connected():
            connection.rollback()

        flash(
            "Something went wrong while saving your enquiry.",
            "error",
        )
        return redirect(url_for("home") + "#booking")

    finally:
        # Always close the database resources.
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    # -------------------------------------
    # SEND EMAIL AFTER SUCCESSFUL DB SAVE
    # -------------------------------------

    email_sent = send_booking_email(
        booking_id=booking_id,
        name=name,
        phone=phone,
        email=email,
        pickup=pickup,
        destination=destination,
        travel_date=travel_date,
        trip_type=trip_type,
        car_type=car_type,
        passengers=passengers,
        requirements=requirements,
    )

    # Display ONE message based on the email result.
    if email_sent:
        flash(
            f"Thank you! Your enquiry #{booking_id} has been saved "
            "and the notification email was sent.",
            "success",
        )
    else:
        flash(
            f"Your enquiry #{booking_id} has been saved, but the "
            "email notification failed. Please contact us directly.",
            "error",
        )

    return redirect(url_for("home") + "#booking")


# -----------------------------------------
# RUN APPLICATION
# -----------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
