import io
import os
from flask import (Flask, render_template, request, session,
                   redirect, url_for, send_file)
from data_loader import (load_employee_data, load_competencies,
                          get_competencies_for_role_band,
                          GENERAL_QUESTIONS, EXPLORE_OPTIONS, BANDS)
from db import init_db, save_submission
from pdf_generator import generate_pdf

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Load data once at startup ────────────────────────────────────────────────
employees, employee_dict = load_employee_data()
competency_sheets = load_competencies()

# ── Init DB tables (safe if already exist) ───────────────────────────────────
try:
    init_db()
except Exception as e:
    print(f"[WARN] DB init skipped: {e}")


# ── Helper ────────────────────────────────────────────────────────────────────
def _emp_ctx():
    return {
        'emp_code':      session.get('emp_code', ''),
        'emp_name':      session.get('emp_name', ''),
        'role':          session.get('role', ''),
        'role_function': session.get('role_function', ''),
        'team_leader':   session.get('team_leader', ''),
        'division':      session.get('division', ''),
        'vertical':      session.get('vertical', ''),
        'band':          session.get('band', ''),
    }


# ── Step 1: Select Employee ───────────────────────────────────────────────────
@app.route('/')
def step1():
    session.clear()
    return render_template('step1_employee.html', employees=employees)


# ── Step 2: Confirm + Select Band ─────────────────────────────────────────────
@app.route('/step2', methods=['POST'])
def step2():
    emp_code = request.form.get('emp_code', '').strip()
    if emp_code in employee_dict:
        emp = employee_dict[emp_code]
        for k, v in emp.items():
            session[k] = v
    return render_template('step2_band.html', bands=BANDS, emp=_emp_ctx())


# ── Step 3: General Reflection Questions ─────────────────────────────────────
@app.route('/step3', methods=['POST', 'GET'])
def step3():
    if request.method == 'POST' and 'band' in request.form:
        band = request.form.get('band', '')
        if band in BANDS:
            session['band'] = band
    return render_template('step3_general.html',
                           questions=GENERAL_QUESTIONS,
                           explore_options=EXPLORE_OPTIONS,
                           saved=session.get('general_answers', {}),
                           emp=_emp_ctx())


# ── Step 4: Competency Questions ─────────────────────────────────────────────
@app.route('/step4', methods=['POST'])
def step4():
    general = {}
    for i in range(len(GENERAL_QUESTIONS)):
        key = f'q{i+1}'
        if i == 6:
            general[key] = request.form.getlist(key)
        else:
            general[key] = request.form.get(key, '').strip()
    session['general_answers'] = general

    role_function = session.get('role_function', '')
    band = session.get('band', '')
    comps = get_competencies_for_role_band(competency_sheets, role_function, band)
    session['competencies'] = comps

    saved_comp = session.get('competency_answers', {})
    return render_template('step4_competency.html',
                           competencies=comps,
                           saved=saved_comp,
                           emp=_emp_ctx())


# ── Step 5: Preview ───────────────────────────────────────────────────────────
@app.route('/step5', methods=['POST'])
def step5():
    comps = session.get('competencies', [])
    comp_answers = {}
    for i, comp in enumerate(comps):
        comp_answers[str(i)] = {
            'competency':  comp['competency'],
            'attribute':   comp['attribute'],
            'description': comp['description'],
            'indicator':   comp['indicator'],
            'rating':      request.form.get(f'rating_{i}', '5'),
            'reflection':  request.form.get(f'reflection_{i}', '').strip(),
        }
    session['competency_answers'] = comp_answers

    return render_template('step5_preview.html',
                           emp=_emp_ctx(),
                           general_questions=GENERAL_QUESTIONS,
                           explore_options=EXPLORE_OPTIONS,
                           general_answers=session.get('general_answers', {}),
                           comp_answers=list(comp_answers.values()))


# ── Edit redirect (from preview back to step 3) ───────────────────────────────
@app.route('/edit')
def edit():
    return redirect(url_for('step3'))


# ── Submit: save to SQL then show download page ───────────────────────────────
@app.route('/submit', methods=['POST'])
def submit():
    error = None
    submission_id = None
    try:
        submission_id = save_submission(dict(session))
        session['submission_id'] = submission_id
    except Exception as e:
        error = str(e)
    return render_template('step6_complete.html',
                           emp=_emp_ctx(),
                           submission_id=submission_id,
                           error=error)


# ── PDF Download ──────────────────────────────────────────────────────────────
@app.route('/download_pdf')
def download_pdf():
    pdf_bytes = generate_pdf(dict(session), GENERAL_QUESTIONS, EXPLORE_OPTIONS)
    filename = (
        f"Reflection_{session.get('emp_name','Employee').replace(' ','_')}"
        f"_{session.get('band','')}.pdf"
    )
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
