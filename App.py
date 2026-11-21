from flask import Flask, render_template, request, redirect, url_for

app = flask.Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")