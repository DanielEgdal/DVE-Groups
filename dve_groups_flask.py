from flask import session, Flask, render_template,request,redirect,url_for,jsonify,Response,send_file,make_response,send_file, flash
import json, re
from markupsafe import escape
from secret_key import secret_key
from WCIFManipGroups import *
from run_main import *
import io
import zipfile

app = Flask(__name__)

app.config.update(
    SECRET_KEY = secret_key,
    SESSION_COOKIE_SECURE = True,
    PERMANENT_SESSION_LIFETIME = 7200
)

@app.before_request
def give_name():
    if 'name' not in session:
        session['name'] = None
    if 'id' not in session:
        session['id'] = None

@app.route('/')
def home():
    return render_template('index.html',user_name=session['name'])

@app.route('/logout',methods=['GET','POST'])
def logout():
    keys = [key for key in session.keys()]
    for key in keys:
        session.pop(key)
    return redirect(url_for('home'))
        

@app.route('/show_token')
def show_token():
    return render_template('show_token.html',user_name=session['name'])

@app.route('/process_token',methods=['POST'])
def process_token():
    access_token_temp = escape(request.form['access_token'])
    access_token= access_token_temp.split('access_token=')[1].split('&')[0]
    session['token'] = {'Authorization':f"Bearer {access_token}"}
    return "Redirect should be happening to /me. Otherwise do it manually."

@app.route('/localhost')
def localhost():
    return redirect("https://www.worldcubeassociation.org/oauth/authorize?client_id=8xB-6U1fFcZ9PAy80pALi9E7nzfoF44W4cMPyIUXrgY&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fshow_token&response_type=token&scope=manage_competitions+public")

@app.route('/me', methods = ['POST', 'GET'])
def logged_in():
    if request.method == 'POST':
        token = escape(request.form['token'])
        session['token'] = {'Authorization':f"Bearer {token}"}
    if 'token' in session:
        if not session['name']:
            me = get_me(session['token'])
            if me.status_code == 200:
                user_name = json.loads(me.content)['me']['name']
                user_id = int(json.loads(me.content)['me']['id'])
                session['name'] = user_name
                session['id'] = user_id
            else:
                return f"Some error occured: {me.status_code}, {me.content}"
        comps = get_coming_comps(session['token'],session['id'])
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
                if wcif['extensions']:
                    if 'stations' in wcif['extensions'][0]['data']:
                        session['pre_stations'] = wcif['extensions'][0]['data']['stations']
                    else:
                        session['pre_stations'] = 10
                else:
                    session['pre_stations'] = 10
            else:
                session['canAdminComp'] = False
                session['pre_stations'] = None
                statusCode = 401
            return render_template("group_spec.html",compid=compid,user_name=session['name'],status=statusCode,admin=(session['canAdminComp']),pre_stations = session['pre_stations'])
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
                form_data = request.form
                session['stations'] = int(escape(form_data["stations"]))
                session['stages'] = int(escape(form_data["stages"]))
                session['combinedEvents'] = escape(form_data["combinedEvents"]).strip().lower()
                session['eventGroups'] = escape(form_data["eventGroups"]).strip().lower()
                if not session['combinedEvents']:
                    session['combinedEvents'] = [[]]
                else:
                    setsOfCombEvents = session['combinedEvents'].split('-')
                    allOfCombEvents = []
                    for sett in setsOfCombEvents:
                        allOfCombEvents.append([event.strip() for event in sett.split(',')])
                    session['combinedEvents'] = allOfCombEvents
                if not session['eventGroups']:
                    session['eventGroups'] = {}
                else:
                    eventGroupString = session['eventGroups'].split(',')
                    temp = {}
                    for pair in eventGroupString:
                        event, groupCount = pair.split(':')
                        groupCount = int(groupCount)
                        temp[event] = groupCount
                    session['eventGroups'] = temp
                if session['canAdminComp']:
                    wcif,statusCode =  getWcif(compid,session['token'])
                    session['postToWCIF'] = True if request.form.getlist("postToWCIF") else False
                    pdfs_to_user = callAll(wcif,header= session['token'],customGroups=session['eventGroups'],stations=session['stations'],authorized=session['canAdminComp'], stages=session['stages'], postWCIF=session['postToWCIF'],allCombinedEvents=session['combinedEvents'])
                else:
                    wcif,statusCode =  getWCIFPublic(compid)
                    session['postToWCIF']  = False
                    pdfs_to_user = callAll(wcif,header= None,stations=session['stations'],customGroups=session['eventGroups'],authorized=session['canAdminComp'], stages=session['stages'], postWCIF=session['postToWCIF'],allCombinedEvents=session['combinedEvents'])
                
                
                
                if session['stages'] > 1: # This is because scorecards might be stored as zip. Rest of files is done below.
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
        else:
            return fail_string
    return fail_string

@app.route("/comp/<compid>/existing_groups",methods=['POST'])
def existing_groups_flask(compid):
    fail_string = "The ID you have hardcoded into the URL doesn't match a valid format of a competition url."
    escapedCompid = escape(compid)
    if len(escapedCompid) <= 32:
        pattern = re.compile("^[a-zA-Z\d]+$")
        if pattern.match(escapedCompid):
            if session['canAdminComp']:
                wcif,statusCode =  getWcif(compid,session['token'])
            else:
                wcif,statusCode =  getWCIFPublic(compid)
            form_data = request.form
            session['stages'] = int(escape(form_data["stages"]))
            
            pdfs_to_user = existing_groups(wcif,session['canAdminComp'],session['stages'])

            if session['stages'] > 1: # This is because scorecards might be stored as zip. Rest of files is done below.
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
        else:
            return fail_string
    return fail_string
    

@app.route("/wcif-extensions/CompetitionConfig.json")
def spec_url():
    data = {'description':"The tool used to generate scorecards for most first rounds. More documentation will follow later. This is kind of a mess rn."
            }
    return jsonify(data)

@app.route("/wcif-extensions/CombinedEvents")
def combinedEventsExplanation():
    data = {"description":"Force competitors to be assigned in the same group and at the same station for all events you list. This will also give them judging assignments in all groups of these events (except when they are competing). Remember that you have to use event IDs!",
            "options":{
        'Empty':"Not writing anything in the field will ignore the feature.",
            "All":"Writing `all` will assume all events are held at the same time.",
            "One set":"You will have to comma seperate all the events. E.g. `333,222,444` means these 3 events are held at the same time.",
            "Multiple sets":"You will be using both comma and dash seperation. The dash splits up into different sets, such that the seperations of the dash will mean those event sets are held at the same time. E.g. `333,222-444,555` means that 4x4 and 5x5 are held at the same time, and 3x3 and 2x2 are held at the same time.",}
            }
    return jsonify(data)
    
@app.route("/wcif-extensions/CustomGroups")
def CustomGroupsExplanation():
    data = {"description":"Force events to have a specific amount of groups, regardless of the stations available. Events not mentioned will have the amount of groups determined by the amount of stations. Remember that you have to use event IDs!",
            "options":{
        'Empty':"Not writing anything in the field will ignore the feature.",
            "One specification":"You will write a colon `:` between the event and the amount of groups. E.g. `pyram:3` means 3 groups of pyraminx",
            "Multiple specifications":"You will write a colon `:` between the event and the amount of groups, and have to comma seperate all the events. E.g. `pyram:3,skewb:2` means 3 groups of pyraminx, and 2 groups of skewb.",}
            }
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5000,debug=True)