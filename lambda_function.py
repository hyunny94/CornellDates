# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from utils import get_default_academic_year, pick_closest_event_for_grade

import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_ACADEMIC_YEAR = get_default_academic_year()
DEFAULT_LOCATION = "ithaca"
DEFAULT_GRADE = "freshman"
DYNAMODB_TABLE_NAME = "CornellDates" + DEFAULT_ACADEMIC_YEAR
SSML_START = "<speak>"
SSML_EMPHASIS_STRONG_START = '<emphasis level="strong">'
SSML_EMPHASIS_STRONG_END = '</emphasis>'
SSML_EMPHASIS_MODERATE_START = '<emphasis level="moderate">'
SSML_EMPHASIS_MODERATE_END = '</emphasis>'
SSML_END = "</speak>"


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can say Hello or Help. Which would you like to try?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello Luke!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class WhenIsEventIntentHandler(AbstractRequestHandler):
    """Handler for WhenIsEvent Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("WhenIsEvent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # 1. Retrieve slots from alexa
        slots = handler_input.request_envelope.request.intent.slots
        if slots['DeadlineEvent'].resolutions:
            if slots['DeadlineEvent'].resolutions.resolutions_per_authority[0].values:
                event_abb_name = slots["DeadlineEvent"].resolutions.resolutions_per_authority[0].values[0].value.name
            else:
                raise Exception("sorry we have the event on record but can you try rephrasing your question?")
        elif slots['PeriodEvent'].resolutions:
            if slots['PeriodEvent'].resolutions.resolutions_per_authority[0].values:
                event_abb_name = slots["PeriodEvent"].resolutions.resolutions_per_authority[0].values[0].value.name
            else:
                raise Exception("sorry we have the event on record but can you try rephrasing your question?")
        elif slots['ReleaseEvent'].resolutions:
            if slots['ReleaseEvent'].resolutions.resolutions_per_authority[0].values:
                event_abb_name = slots["ReleaseEvent"].resolutions.resolutions_per_authority[0].values[0].value.name
            else:
                raise Exception("sorry we have the event on record but can you try rephrasing your question?")
        else:
            raise Exception("sorry we cannot answer the question at this time.")

        # 2. Query the dynamoDB
        try:
            client = boto3.client('dynamodb')
            response = client.query(
                ExpressionAttributeValues={
                    ':v1': {
                        'S': event_abb_name,
                    },
                },
                KeyConditionExpression="event_abb_name = :v1",
                TableName=DYNAMODB_TABLE_NAME,
            )
            print(response)
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            event = pick_closest_event_for_grade(response['Items'], DEFAULT_GRADE)

        # 3. format the answer
        date_granularity = event['date_granularity']['S']
        internal_category = event['internal_category']['S']
        start = int(event['start']['N'])
        speak_output = SSML_START
        speak_output += event_abb_name
        # depending on 
        # 3.1 this event's ['date_granularity'] => one of ["date", "hour"]
        if internal_category == 'period':
            end = int(event['end']['N'])
            if date_granularity == "date":
                start = time.strftime('%Y-%m-%d', time.localtime(start))
                end = time.strftime('%Y-%m-%d', time.localtime(end))
            elif date_granularity == "hour": 
                start = time.strftime('%Y-%m-%d %H:%M', time.localtime(start))
                end = time.strftime('%Y-%m-%d %H:%M', time.localtime(end))
        elif internal_category == 'release':
            if date_granularity == "date":
                start = time.strftime('%Y-%m-%d', time.localtime(start))
            elif date_granularity == "hour": 
                start = time.strftime('%Y-%m-%d %H:%M', time.localtime(start))
        else: # internal_category == 'deadline'
            if date_granularity == "date":
                start = time.strftime('%Y-%m-%d', time.localtime(start))
            elif date_granularity == "hour": 
                start = time.strftime('%Y-%m-%d %H:%M', time.localtime(start))
        
        # 3.2 this event's ['internal_category'] => "period" means the event has "start" and "end"
        if internal_category == 'period':
            speak_output += " is from " +\
                 SSML_EMPHASIS_MODERATE_START + start + SSML_EMPHASIS_MODERATE_END +\
                      " until " +\
                           SSML_EMPHASIS_MODERATE_START + end + SSML_EMPHASIS_MODERATE_END
        else:
            speak_output += " is on " +\
                SSML_EMPHASIS_MODERATE_START + start + SSML_EMPHASIS_MODERATE_END

        speak_output += SSML_END

        # 4. respond
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(WhenIsEventIntentHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers


sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
