from flask import (Flask, redirect, render_template, request, send_file, session, url_for, send_from_directory, make_response, jsonify)
import os

from utils.database import ProspectiveQAs, DueQAs, ScribeData, load_prospective_qas, load_divisions, load_qa_tracks, load_assessors, _convert_division_long_short, prospective_dropdown_display

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    # prospective variables needs
    # prospective - list of prospective QA data as lists per QA

    # due - list of due QAs needed per alogirthm

    # stats? down the line

    return redirect(url_for('home'))


@app.route('/home')
def home():
    """ Home page for redirection """
    prospective_qas = load_prospective_qas()
    all_divisions = load_divisions()
    all_qat_names = load_qa_tracks()
    all_assessors = load_assessors()
    
    # need render variables: due
    return render_template('home.html', prospective=prospective_qas, divisions=all_divisions, qats=all_qat_names, assessors=all_assessors)

@app.route('/submit_prospective', methods=['POST'])
def submit_qa():
    # add proseptive QA
    # redirect to home page to reload
    # print(request.form['qaf-scribe'])

    new = ProspectiveQAs()
    new.add_prospective(request.form['qaf-scribe'], request.form['qaf-date'], request.form['qaf-division'], request.form['qaf-assessor'], request.form['qaf-provider'], request.form['qaf-comments'])
    return redirect(url_for('home'))





@app.route('/add_new_scribe', methods=['POST'])
def add_scribe():
    new = ScribeData()
    new.add_scribe(name=request.form['nsf-scribe'], division=request.form['nsf-division'], qat=request.form['nsf-qat'], solo=request.form['nsf-solo-date'], ffts=request.form['nsf-ffts'])
    return redirect(url_for('home'))




# TODO Works but will error if re-choose an option
@app.route('/get_scribes_providers_per_division', methods=['POST', 'GET'])
def populate_scribe_divisions_dropdown():
    div_sn = _convert_division_long_short(request.json['division'])
    data = prospective_dropdown_display(div_sn)
    print(f'data: {data}')
    return jsonify(data)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)