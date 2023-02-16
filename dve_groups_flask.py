from flask import session, Flask, render_template,request,url_for,send_file,Response,make_response,send_file
import json, re
from markupsafe import escape
# from old import *
from WCIFManip import *
from run_main import *
import io
import zipfile

app = Flask(__name__)
# TODO, Change before running on server
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
            session['name'] = user_name
            comps = get_coming_comps(session['token'])
            return render_template('logged_in.html',data=user_name,comps=comps)
        else:
            return f"Some error occured: {me.status_code}, {me.content}"
    else:
        return "You are currently not authorized. Either go to the playground or ensure you are logged in."

@app.route('/playground')
def playground():
    temp_name = "Not logged in"
    if 'name' in session:
        temp_name = session['name']
    return render_template('playground.html',name=temp_name)

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
                session['stations'] = int(escape(form_data["stations"]))
                session['stages'] = int(escape(form_data["stages"]))
                session['combinedEvents'] = form_data["combinedEvents"]
                session['postToWCIF'] = request.form.getlist("postToWCIF")
                wcif =  getWcif(compid,session['token']) # TODO Make some check if the person has admin rights
                
                pdfs_to_user = callAll(wcif,session['stations'],stages=session['stages'])
                
                if session['stages'] > 1:
                    scorecardObj = pdfs_to_user.pop()
                    scorecardZip = zipfile.ZipFile(io.BytesIO(scorecardObj[-1]))
                    for name in scorecardZip.namelist():
                        with scorecardZip.open(name, 'r') as pdf_file:
                            pdfs_to_user.append((name,pdf_file.read()))
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for file_name,data in pdfs_to_user:
                        zip_file.writestr(file_name, data)

                return Response(zip_buffer.getvalue(),mimetype="application/zip",headers={'Content-Disposition': f'attachment;filename={compid}Files.zip'})
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