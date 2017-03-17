# -*- coding: utf-8 -*-

import collections
import json
import logging
import traceback
import flask
from google.cloud import language

# My modules
import wikipediautil
import qclf

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

app = flask.Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Set log level
logging.basicConfig(level=logging.DEBUG)


@app.route("/", methods=["GET"])
def main():
    return "ok"


@app.route("/qa", methods=["GET"])
def api():
    question = flask.request.args.get("question")
    if not question:
        question = "where is the capital of Japan?"
    # Extract keywords from question
    search_keywords = extract_keywords(question)
    # Choose question type from {"PERSON", "LOCATION", "ORGANIZATION"}
    question_type = qclf.SimpleQuestionClassifier().predict(question)
    # Search Wikipedia
    res_titles = wikipediautil.search_titles(" ".join(search_keywords))
    page_title = res_titles["query"]["search"][0]["title"].encode("utf-8")
    res_contents = wikipediautil.search_contents(page_title)
    wikipedia_content = res_contents["query"]["pages"].values()[0]["revisions"][0]["*"]
    # Extract candidates
    candidates = extract_candidates(wikipedia_content, question_type)
    # Score candidates
    candidates_with_score = score_candidates(search_keywords, candidates, wikipedia_content)
    # Response
    res = {
        "question": question,
        "type": question_type,
        "candidates": candidates_with_score,
        "search_keyword": search_keywords,
        "wikipedia_title": page_title,
        "wikipedia_content": wikipedia_content
    }
    return flask.jsonify(res)


@app.errorhandler(500)
def page_not_found(error):
    logging.error("oh my god")
    logging.error(traceback.format_exc())
    return "ng", 500


def extract_keywords(question):
    nl_client = language.Client()
    document = nl_client.document_from_text(question)
    syntax_response = document.analyze_entities()
    search_keywords = [entity.name.encode("utf-8") for entity in syntax_response.entities]
    return search_keywords


def extract_candidates(text, question_type):
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
            "extractDocumentSentiment": False
        },
        "encodingType": "UTF8"
    }
    service_request = service.documents().annotateText(body=payload)
    logging.info("run")
    nl_response = service_request.execute()
    # logging.info("__NL_RESPONSE__: {}".format(json.dumps(nl_response)))
    # Score the entities
    candidates = []
    for entity in nl_response["entities"]:
        if entity["type"] == question_type and entity["mentions"][0]["type"] == "PROPER":
            candidates.append(entity["name"])
    return candidates


def score_candidates(search_keywords, candidates, wikipedia_content):
    candidates_with_score = {}
    # Replace space to underscore
    for cand in candidates:
        wikipedia_content = wikipedia_content.replace(cand, cand.replace(" ", "_"))
    words = wikipedia_content.split(" ")
    for cand in candidates:
        for i, word in enumerate(words):
            if cand.replace(" ", "_") in word:
                marginal_words = words[max(i - 15, 0):min(i + 15, len(words))]
                logging.info(cand)
                logging.info(marginal_words)
                score = len(set.intersection(set(marginal_words), set(search_keywords)))
                if not candidates_with_score.has_key(cand):
                    candidates_with_score[cand] = 0
                candidates_with_score[cand] += score
    logging.info(candidates_with_score)
    res = collections.Counter(candidates_with_score).most_common(100)
    logging.info(res)
    return dict(res)
