from google.cloud.language import enums
from google.cloud.language import LanguageServiceClient
from google.cloud.translate import Client as TranslateClient
import six
import sys


def analyze(content):
    translate_client = TranslateClient()
    language_client = LanguageServiceClient()

    if isinstance(content, six.binary_type):
        content = content.decode('utf-8')

    translation = translate_client.translate(content, target_language='en')

    document = {'type': enums.Document.Type.PLAIN_TEXT, 'content': translation['translatedText']}
    response = language_client.analyze_sentiment(document)
    sentiment = response.document_sentiment

    print('Translation: {}'.format(translation['translatedText']))
    print('Score: {}'.format(sentiment.score))
    print('Magnitude: {}'.format(sentiment.magnitude))


analyze(sys.argv[1])
