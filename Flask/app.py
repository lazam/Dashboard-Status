from flask import Flask, request, redirect, session, url_for, render_template
from flask.json import jsonify

import os, json, sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('layout.html')

@app.route("/pipelines", methods=['GET', 'POST'])
def pipelines():
    if request.method == 'POST':
        data = request.get_json()
        repo_name = data['repository']['name']
        commit_author = data['commit_status']['commit']['author']['raw']
        build_status = data['commit_status']['state']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        
        c.execute("SELECT * FROM pipelines WHERE name = ?", [repo_name])

        if len(c.fetchall()) > 0:
            c.execute("UPDATE pipelines SET status = ? WHERE name = ?", (build_status, repo_name))
        else:
            c.execute("INSERT INTO pipelines(name, author, status) VALUES(?, ?, ?)", (repo_name, commit_author, build_status))

        conn.commit()
        c.close()
        conn.close()

    return render_template('pipelines.html')

@app.route("/pullrequests", methods=['GET', 'POST'])
def commits():
    if request.method == 'POST':
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        
        data = request.get_json()
        approval_count = 0
        repo_name = data['pullrequest']['destination']['repository']['name']
        pr_approval = data['pullrequest']['participants']
        pr_author = data['pullrequest']['author']['username']
        pr_state = data['pullrequest']['state']
        pr_branch = data['pullrequest']['source']['branch']['name']
        
        c.execute("SELECT * FROM pullrequests WHERE branch = ? AND name = ?", (pr_branch, repo_name))
        pr_data = (c.fetchall())

        if len(pr_data) > 0:
            if pr_state == "OPEN":
                for num in range(len(pr_approval)):
                    if pr_approval[num]['approved'] == True:
                        approval_count += 1
                c.execute("UPDATE pullrequests SET approval = ?, state = ? WHERE branch = ? AND name = ?", (approval_count, pr_state, pr_branch, repo_name))
            else:
                c.execute("UPDATE pullrequests SET state = ? WHERE branch = ? AND name = ?", (pr_state, pr_branch, repo_name))

        else:
            c.execute("INSERT INTO pullrequests(name, author, state, branch, approval) VALUES(?, ?, ?, ?, ?)", (repo_name, pr_author, pr_state, pr_branch, approval_count))

        conn.commit()
        c.close()
        conn.close()

    return render_template('pullrequests.html')

@app.route("/pr_list")
def commits_list():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('SELECT * FROM pullrequests')

    pullrequests = c.fetchall()

    conn.close()

    return render_template('pullrequests.html', pullrequests=pullrequests)

@app.route("/pipeline_list")
def pipeline_list():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('SELECT * FROM pipelines')

    pipelines = c.fetchall()

    conn.close()

    return render_template('pipelines.html', pipelines=pipelines)


@app.route("/db_create")
def create_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS pipelines(name TEXT, author TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS pullrequests(name TEXT, author TEXT, state TEXT, branch TEXT, approval INTEGER)')
    
    conn.commit()
    c.close()
    conn.close()

    return "DB Created!"

@app.route("/db_cleanup")
def cleanup_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('DELETE FROM pullrequests WHERE state = "MERGED"')
    c.execute('DELETE FROM pullrequests WHERE state = "DECLINED"')
    c.execute('DELETE FROM pipelines WHERE status = "SUCCESSFUL"')

    conn.commit()
    c.close()
    conn.close()

    return "DB Cleanup!"
    
if __name__ == '__main__':
    app.secret_key = 'testasd'
    app.run(host='0.0.0.0')