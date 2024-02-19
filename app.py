from flask import (Flask, redirect, render_template, request, send_file, session, url_for, send_from_directory, make_response)
import os

from utils.database import ProspectiveQAs, DueQAs, ScribeData

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    # prospective variables needs
    # prospective - list of prospective QA data as lists per QA

    # due - list of due QAs needed per alogirthm

    # stats? down the line

    return render_template('home.html')

@app.route('/home')
def home():
    """ Home page for redirection """
    return render_template('home.html', prospective=[('Therry Malone', '12/1/21', 'MED', 'Lerty', 'Zaki'), ('Therry Malone', '12/1/21', 'MED', 'Lerty', 'Zaki')])

@app.route('/submit_prospective', methods=['POST'])
def submit_qa():
    # add proseptive QA
    # redirect to home page to reload
    new = ProspectiveQAs()
    new.add_prospective(request.form['qaf-scribe'], request.form['qaf-date'], request.form['qaf-division'], request.form['qaf-assessor'], request.form['qaf-provider'], request.form['qaf-comments'])
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)