# -*- coding: utf-8 -*-

import collections
import json
import logging
import traceback
import flask
from google.cloud import language, translate
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# My modules
import wikipediautil
import qclf


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
    rep = reply_factoid(question)
    res = flask.render_template(
        "result.html",
        question=rep["question"],
        translated_question=rep["translatedQuestion"],
        question_type=rep["questionType"],
        wikipedia_title=rep["wikipediaTitle"].decode("utf-8"),
        query_words=json.dumps(rep["queryWords"]),
        candidates=json.dumps(collections.Counter(rep["candidates"]).most_common(5), ensure_ascii=False)
    )
    return res


@app.route("/api/factoid", methods=["GET"])
def api_factoid():
    question = flask.request.args.get("question")
    if not question:
        question = "where is the capital of Japan?"
    res = reply_factoid(question)
    return flask.jsonify(res)


def reply_factoid(question):
    # Translate to English
    translated_question = translate_text_to_english(question)
    # Extract query words from question
    entity_response = extract_entities(translated_question)
    query_words = [entity.name for entity in entity_response.entities]
    # Choose question type from {"PERSON", "LOCATION"}
    question_type = qclf.SimpleQuestionClassifier().predict(translated_question)
    if (not query_words) or (question_type == "OTHER"):
        candidates = []
        page_title = wikipedia_content = None
    else:
        # Search Wikipedia title
        logging.info("Search Wikipedia title...")
        res_titles = wikipediautil.search_titles(" ".join(query_words))
        page_title = res_titles["query"]["search"][0]["title"].encode("utf-8")
        # Search Wikipedia content
        logging.info("Search Wikipedia content...")
        wikipedia_content = wikipediautil.search_contents(page_title)
        candidates = extract_candidates(wikipedia_content, question_type, query_words)
    # Response
    res = {
        "question": question,
        "translatedQuestion": translated_question,
        "questionType": question_type,
        "candidates": candidates,
        "queryWords": query_words,
        "wikipediaTitle": page_title,
        "wikipediaContent": wikipedia_content
    }
    return res


@app.errorhandler(500)
def server_error(e):
    logging.error(traceback.format_exc())
    return "Server Error :(", 500


def extract_entities(text):
    nl_client = language.Client()
    document = nl_client.document_from_text(text)
    entities = document.analyze_entities()
    return entities


def extract_candidates(text, question_type, query_words):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build("language", "v1", credentials=credentials)
    payload = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        },
        "features": {
            "extractSyntax": False,
            "extractEntities": True,
            "extractDocumentSentiment": True
        },
        "encodingType": "UTF8"
    }
    service_request = service.documents().annotateText(body=payload)
    nl_response = service_request.execute()
    candidates = {}
    for entity in nl_response["entities"]:
        score = 0
        if entity["type"] != question_type:
            continue
        for mention in entity["mentions"]:
            if mention["type"] == "COMMON":
                # continue
                break
            for sentence in nl_response["sentences"][::-1]:
                words_in_sentence = sentence["text"]["content"].split(" ")
                if sentence["text"]["beginOffset"] <= mention["text"]["beginOffset"]:
                    score += sum(words_in_sentence.count(i) for i in query_words)
                    break
        candidates[entity["name"]] = score
    return candidates


def translate_text_to_english(text):
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language="en")
    return result['translatedText']
