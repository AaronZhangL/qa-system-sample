# -*- coding: utf-8 -*-


class SimpleQuestionClassifier:

    def __init__(self):
        pass

    @staticmethod
    def predict(question):
        if "who" in question.lower():
            return "PERSON"
        elif "where" in question.lower():
            return "LOCATION"
        else:
            return "OTHER"
