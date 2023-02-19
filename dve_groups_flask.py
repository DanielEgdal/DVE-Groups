from flask import session, Flask, render_template,request,redirect,url_for,send_file,Response,make_response,send_file, flash
import json, re
from markupsafe import escape
from urllib.parse import urlparse, parse_qs
# from old import *
import os
from secrets import token_hex
from WCIFManip import *
from run_main import *
import io
import zipfile

app = Flask(__name__)

key = token_hex()
app.config.update(
    SECRET_KEY = key,
    SESSION_COOKIE_SECURE = True
)

@app.route('/')
def home():
    if 'name' not in session:
        session['name'] = None
    return render_template('index.html',user_name=session['name'])

@app.route('/logout',methods=['GET','POST'])
def logout():
    keys = [key for key in session.keys()]
    for key in keys:
        session.pop(key)
    return redirect(url_for('home'))
        

@app.route('/show_token') # If we can get SSL/Https, then this function might be able to display the code. Or better, oauth can happen as intended.
def show_token():
    return render_template('show_token.html',user_name=session['name'])

@app.route('/process_token',methods=['POST'])
def process_token():
    access_token_temp = request.form['access_token']
    access_token= access_token_temp.split('access_token=')[1].split('&')[0]
    session['token'] = {'Authorization':f"Bearer {access_token}"}
    return "Redirect should be happening to /me. Otherwise do it manually."

@app.route('/me', methods = ['POST', 'GET'])
def logged_in(): # TODO, make some checks that the code is valid and not malicous
    # if request.method == 'POST':
    #     form_data = request.form
    #     session['token'] = {'Authorization':f"Bearer {form_data['token']}"}
    if 'token' in session: # TODO, doesn't make sense with the rest of the flow, fix
        if not session['name']:
            me = get_me(session['token'])
            if me.status_code == 200:
                user_name = json.loads(me.content)['me']['name']
                session['name'] = user_name
            else:
                return f"Some error occured: {me.status_code}, {me.content}"
        comps = get_coming_comps(session['token'])
        return render_template('logged_in.html',user_name=session['name'],comps=comps)   
    else:
        return "You are currently not authorized. Either go to the playground or ensure you are logged in."

@app.route('/playground')
def playground():
    return render_template('playground.html',user_name=session['name'])

@app.route("/comp/<compid>")
def comp_page(compid):
    fail_string = "The ID you have hardcoded into the URL doesn't match a valid format of a competition url."
    escapedCompid = escape(compid)
    if len(escapedCompid) <= 32:
        pattern = re.compile("^[a-zA-Z\d]+$")
        if pattern.match(escapedCompid):
            if 'token' in session:
                wcif,statusCode =  getWcif(compid,session['token'])
                session['canAdminComp'] = True if statusCode == 200 else False
            else:
                session['canAdminComp'] = False
                statusCode = 401
            return render_template("group_spec.html",compid=compid,user_name=session['name'],status=statusCode,admin=(session['canAdminComp']))
        else:
            return fail_string
    return fail_string

@app.route("/comp/<compid>/download", methods = ['POST'])
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
                if session['canAdminComp']:
                    wcif,statusCode =  getWcif(compid,session['token'])
                    session['postToWCIF'] = True if request.form.getlist("postToWCIF") else False
                    # print(session['postToWCIF'])
                else:
                    wcif,statusCode =  getWCIFPublic(compid)
                    session['postToWCIF']  = False
                
                pdfs_to_user = callAll(wcif,header= session['token'],stations=session['stations'],authorized=session['canAdminComp'], stages=session['stages'], postWCIF=session['postToWCIF'])
                
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
                zipFiles = Response(zip_buffer.getvalue(),mimetype="application/zip",headers={'Content-Disposition': f'attachment;filename={compid}Files.zip'})
                return zipFiles
                # return redirect(url_for("comp_page",compid=compid),303,zipFiles)
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
    
# app.run(debug=True)

if __name__ == '__main__':
    app.run(port=5000)