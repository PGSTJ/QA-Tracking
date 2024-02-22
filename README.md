# QA-Tracking

## Description
The QA Tracker is a web application designed to track Quality Assurance (QA) reports/shifts, specifically for medical scribes at CHLA. It allows users to manage prospective QAs, view upcoming due dates, and access statistics related to QA activities. 

## Features
* **Prospective QA Tracking:** Users can add and manage prospective QAs by specifying the date, scribe being QA'd, the provider and division, who the assessor is, and any comments QA leads have. Users select the division first to autopopulate all scribes and providers associated with that division.
* **Upcoming Due Dates:** The applcation provides a view of upcoming due dates for QAs, allowing users to stay informed and prepared. There are customizable filter options to view severaly to moderately overdue QAs (1-2 months overdue) to nearly due QAs (within a week of being due) and more.
* **Divisional Navigation:** Users can navigate through all of the divisions to see an overview of scribe QA performance and statistics for that division.
* **Statistics:** The application provides statistical insights into QA reports, giving users a quick snapshot into scribe performance as well as helping to understand trends and patterns overtime.

## Installation
1. Clone the repository to your local machine.
2. Ensure you have Python and Flask installed.
3. Run `pip install -r requirements.txt` go install the required dependencies.
4. Start the Flask server by running `python app.py`.
5. Access the application in your web browser at `http://localhost:5000`.

## Usage
1. Navigate to the home page for an overview of every section: The QA Tracker Board, each division, and general statistics.
2. Add prospective QAs by clicking the "Add Prospective QA" link and filling out the form.
3. View upcoming due dates in the "Due" section of the dashboard.
4. Navigate through different divisions using the provided links
5. Access general and some specific statistics from the home page while more detailed statistics for each division can be found in the division section/pages.

## License
This project is licensed under the GNU General Public License v3.0. See the LICENSE file for more details.
