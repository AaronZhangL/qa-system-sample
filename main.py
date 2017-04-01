# -*- coding: utf-8 -*-

import collections
import json
import logging
import traceback
import flask

import factoid

app = flask.Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Set log level
logging.basicConfig(level=logging.DEBUG)


@app.route("/", methods=["GET"])
def main():
    return flask.render_template("index.html")


@app.route("/result", methods=["GET"])
def show_result():
    question = flask.request.args.get("question".encode("utf-8"))
    rep = factoid.reply(question)
    res = flask.render_template(
        "result.html",
        question=rep["question"],
        translated_question=rep["translatedQuestion"],
        question_type=rep["questionType"],
        wikipedia_title=rep["wikipediaTitle"],
        query_words=json.dumps(rep["queryWords"]),
        candidates=json.dumps(collections.Counter(rep["candidates"]).most_common(5), ensure_ascii=False)
    )
    return res


@app.errorhandler(500)
def server_error(e):
    logging.error(traceback.format_exc())
    return "Server Error :(", 500
