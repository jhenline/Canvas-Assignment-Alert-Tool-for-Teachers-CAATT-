# Canvas Assignment Alert Tool for Teachers (CAATT)

## Author
- **Original Author**: Henry Acevedo
- **Refactored by**: Jeff Henline (2024)

## Overview
The Canvas Assignment Alert Tool for Teachers (CAATT) is designed to assist educators in monitoring and managing ungraded submissions in specified Canvas courses. The tool automates the process of identifying pending submissions and notifying designated recipients via email, streamlining the grading process.

## Purpose
This script monitors pending submissions in the Canvas courses listed in the “caatt” table. Upon detecting ungraded submissions, CAATT automatically sends an email notification to the designated recipients, providing details about the students and links to their ungraded work.

## Features
- **Canvas API Integration**: Connects to the Canvas LMS to monitor course assignments.
- **Automated Email Notifications**: Sends alerts to designated recipients using SendGrid when ungraded submissions are detected.
- **Database Management**: Utilizes a MySQL database to manage course and assignment information.
- **Customizable Configuration**: Easily configure the tool via a `config.ini` file.

## Requirements
- Python 3.x
- Required Python packages:
  - `tabulate`
  - `canvasapi`
  - `configparser`
  - `sendgrid`
  - `mysql-connector-python`
- A configured MySQL database
- A SendGrid API key
- Access to a Canvas LMS instance
