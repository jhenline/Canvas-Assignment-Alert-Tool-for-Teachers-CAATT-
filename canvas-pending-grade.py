# Teacher Canvas Assignment Alert Tool for Teachers (CAATT)
# Henry Acevedo (original Author)
# Refactored by Jeff Henline (2024) for use on AWS and to be managed by database rather than hard-coded
# 
# Purpose: This script monitors pending submissions in specified Canvas courses, as listed in the “caatt” table. 
# Upon detecting ungraded submissions, the tool automatically sends an email notification to the designated 
# recipients, providing details about the students and links to their ungraded work.

from tabulate import tabulate
from canvasapi import Canvas
from configparser import ConfigParser
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import TrackingSettings, ClickTracking
from datetime import datetime
import mysql.connector

# Load the configuration file
config = ConfigParser()
config.read('/home/bitnami/scripts/config.ini')

# Retrieve Canvas instance and token
MYURL = config.get("instance", "prod")
MYTOKEN = config.get("auth", "token")

# Initialize Canvas API
canvas = Canvas(MYURL, MYTOKEN)

# Connect to database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=config.get("mysql", "DB_HOST"),
            database=config.get("mysql", "DB_DATABASE"),
            user=config.get("mysql", "DB_USER"),
            password=config.get("mysql", "DB_PASSWORD")
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Query database to get all active assignment alerts
def get_course_assignments():
    connection = connect_to_database()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                           SELECT course_id, assignment_id, recipients FROM caatt WHERE date_expiration > CURDATE() AND isactive = 1
                           """)
            result = cursor.fetchall()
            return result
        except mysql.connector.Error as e:
            print(f"Error fetching data from MySQL: {e}")
            return []
        finally:
            connection.close()
    else:
        return []

# Email function using SendGrid
def sendEmail(pending_table, recipients, course_id, assignment_id, assignment_name):
    bcc_email = "jhenlin2@calstatela.edu"  # Henline will always be BCC'd

    message = Mail(
        from_email='cetltech@calstatela.edu',
        to_emails=recipients,  # Use the list of recipients
        subject=f'Grading Required: New Submissions for "{assignment_name}"',
        html_content=f"""<h3>The following students have ungraded submissions for "{assignment_name}":</h3>
                        {pending_table}<br>(Email sent via FDMS)<br>"""
    )

    # Add BCC email
    message.add_bcc(bcc_email)

    # Disable link tracking
    tracking_settings = TrackingSettings()
    tracking_settings.click_tracking = ClickTracking(enable=False, enable_text=False)
    message.tracking_settings = tracking_settings

    sg = SendGridAPIClient(config['auth']['sendgrid_api_key'])

    try:
        response = sg.send(message)
        print("Email sent successfully")
        print(f"Response Status Code: {response.status_code}")
        update_date_last_ran(course_id, assignment_id)  # Update the timestamp after successful email send
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# Function to check for ungraded assignments in course(s)
def check_submissions(pending, course_id, assignment_id):
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    assignment_name = assignment.name  # Get the assignment name

    submissions = assignment.get_submissions(include=["user"])
    for sub in submissions:
        if sub.workflow_state == "submitted":
            pending.append({
                'name': sub.user["name"],
                'link': f'https://calstatela.instructure.com/courses/{course.id}/gradebook/speed_grader?assignment_id={assignment.id}&student_id={sub.user_id}',
                'description': 'Click here to grade'
            })
    return pending, assignment_name

# Function to update database with the date_last_ran 
# only logs an update when an email is dispatched
def update_date_last_ran(course_id, assignment_id):
    connection = connect_to_database()
    if connection is not None:
        try:
            cursor = connection.cursor()
            current_time = datetime.now()  # Get the current time
            update_query = """
                UPDATE caatt 
                SET date_last_ran = NOW() 
                WHERE course_id = %s AND assignment_id = %s
            """
            cursor.execute(update_query, (course_id, assignment_id))
            connection.commit()
            print(f"Date last ran updated successfully for course_id: {course_id}, assignment_id: {assignment_id} at {current_time}")
        except mysql.connector.Error as e:
            print(f"Error updating date_last_ran in MySQL for course_id {course_id} and assignment_id {assignment_id}: {e}")
        finally:
            connection.close()
    else:
        print("Failed to connect to the database for updating date_last_ran")

# Main function
def main():
    course_assignments = get_course_assignments()

    for course_id, assignment_id, recipients in course_assignments:
        # Check submissions for each course and assignment
        pending, assignment_name = check_submissions([], course_id, assignment_id)

        if pending:
            # Construct the pending table for each course and assignment
            pending_table = "<ul>"
            for item in pending:
                pending_table += f"<li>{item['name']} - <a href='{item['link']}'>{item['description']}</a></li>"
            pending_table += "</ul>"

            # Split recipients by comma to get a list of email addresses
            recipient_list = recipients.split(',')
            sendEmail(pending_table, recipient_list, course_id, assignment_id, assignment_name)  # Include assignment_name

if __name__ == "__main__":
    main()
