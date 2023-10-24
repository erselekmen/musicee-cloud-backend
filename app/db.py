from flask import Flask
from flask_restplus import Api, Resource

app = Flask(__name__)
api = Api(app, version='1.0', title='Musicee API',
          description='Musicee API documentation powered by Flask RestPlus API')

ns = api.namespace('my_namespace', description='My operations')

@ns.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}
