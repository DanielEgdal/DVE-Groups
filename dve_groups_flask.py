from flask import session, Flask, render_template,request,url_for,send_file,Response,make_response,send_file
import json, re
from markupsafe import escape
# from old import *
from WCIFManip import *
from run_main import *

app = Flask(__name__)
app.secret_key = "please do not hack our good webserver blakd isjdf"

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/show_token')
def show_token():
    return "Hi"

@app.route('/authorized', methods = ['POST', 'GET'])
def logged_in(): # TODO, make some checks that the code is valid and not malicous
    if request.method == 'POST':
        form_data = request.form
        session['token'] = {'Authorization':f"Bearer {form_data['token']}"}
    if 'token' in session:
        me = get_me(session['token'])
        if me.status_code == 200:
            user_name = json.loads(me.content)['me']['name']
            comps = get_coming_comps(session['token'])
            return render_template('logged_in.html',data=user_name,comps=comps)
        else:
            return f"Some error occured: {me.status_code}, {me.content}"
    else:
        return "You are currently not authorized. Either go to the playground or ensure you are logged in."

@app.route("/comp/<compid>")
def comp_page(compid):
    fail_string = "The ID you have hardcoded into the URL doesn't match a valid format of a competition url."
    escapedCompid = escape(compid)
    if len(escapedCompid) <= 32:
        pattern = re.compile("^[a-zA-Z\d]+$")
        if pattern.match(escapedCompid):
            return render_template("group_spec.html",compid=compid)
        else:
            return fail_string
    return fail_string

@app.route("/comp/<compid>/download", methods = ['POST', 'GET'])
def generate_n_download(compid):
    fail_string = "The ID you have hardcoded into the URL doesn't match a valid format of a competition url."
    escapedCompid = escape(compid)
    if len(escapedCompid) <= 32:
        pattern = re.compile("^[a-zA-Z\d]+$")
        if pattern.match(escapedCompid):
            if request.method == 'POST':
                # Escape all of these
                form_data = request.form
                session['stations'] = int(form_data["stations"])
                session['stages'] = form_data["stages"]
                session['combinedEvents'] = form_data["combinedEvents"]
                session['postToWCIF'] = form_data["postToWCIF"] # Check this one
                session['origWCIF'] = getWcif(compid,session['token']) # Make some check if the person has admin rights
                pdf_overview = callAll(session['origWCIF'],session['stations']) # Change this to be more than one file

                # make this much nicer
                # binary = pdf_overview.output(dest='b').decode('latin1')
                binary = pdf_overview.output(dest='b')
                # overview_send = make_response(binary)
                # overview_send.headers['Content-Type'] = 'application/pdf'
                # overview_send.headers['Content-Disposition'] = f'inline; filename={compid}GroupOverview.pdf'

                # session['pdf_overview'] = binary
                # print(session)
                return Response(binary,mimetype="application/pdf",headers={'Content-Disposition': f'attachment;filename={compid}GroupOverview.pdf'})
            # if "pdf_overview" in session:
                # return render_template("files_to_download.html")
            # else:
            #     return "nothing ready for you"
        else:
            return fail_string
    return fail_string

# @app.route("/pdf_overview")
# def get_pdf_overview():
#     if "pdf_overview" in session:
#         # return session['pdf_overiew']
#         return send_file(session['pdf_overiew'])
#     else:
#         print(session)
#         return "You don't have any pdf overview saved"
    
app.run(debug=True)