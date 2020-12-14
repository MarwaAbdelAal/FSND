import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# PAGINATING FUNCTION
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  # Set up CORS. Allow '*' for origins.
  CORS(app, resources={'/': {'origins': '*'}})

  # CORS Headers
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authoriztion,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')

    return response
 
  # Create an endpoint to handle GET requests for all available categories.
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type

    if (len(categories_dict) == 0):
      abort(404)
      
    return jsonify({
      'success': True,
      'categories': categories_dict
    })

  # Create an endpoint to handle GET requests for paginated questions.
  @app.route('/questions')
  def get_questions():
    # get all questions and paginate
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    # get all categories and add to dict
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type
      
    l = list(categories_dict.items())
    current_category = l[-1]

    if len(current_questions) == 0:
      abort(404)
    
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'categories': categories_dict,
      'current_category': current_category
    })

  # Create an endpoint to DELETE question using a question ID. 
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })
    except:
      abort(422)
 
  # Create an endpoint to POST a new question and get questions based on a search term.
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)
    search = body.get('searchTerm', None)

    try:
      if search:
        selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search))).all()
        if (len(selection) == 0):
          return jsonify({
            'success': True,
            'questions': [],
            'total_questions': 0
          })
        current_questions = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(selection)
        })
      
      else:
        question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
        question.insert()

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'created': question.id,
          'question_created': question.question,
          'questions': current_questions,
          'total_questions': len(Question.query.all())
        })

    except Exception as e:
      print(e)
      abort(422)

  # Create a GET endpoint to get questions based on category. 
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    category = Category.query.filter(Category.id == category_id).one_or_none()

    if category is None:
      abort(400)

    selection = Question.query.filter(Question.category == category.id).all()
    current_questions = paginate_questions(request, selection)
    
    return jsonify({
      'success':True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'current_category': category.type
    })

  # Create a POST endpoint to get random questions to play the quiz. 
  @app.route('/quizzes', methods=['POST'])
  def get_random_quiz_question():
    body = request.get_json()
    previous = body.get('previous_questions', None)
    category = body.get('quiz_category', None)

    try:     
      if (category['id'] == 0):
        questions = Question.query.all()
  
      else:
        questions = Question.query.filter(Question.category == category['id']).all()
  
      total_questions = len(questions)
  
      def get_random_question():
        return questions[random.randrange(0, len(questions), 1)]
  
      # checks to see if question has already been used
      def check_if_used(question):
        used = False
        for x in previous:
          if (x == question.id):
            used = True
        return used
  
      question = get_random_question()
  
      while (check_if_used(question)):
        question = get_random_question()
  
        if (len(previous) == total_questions):
          return jsonify({
            'success': True
          })
  
      return jsonify({
        'success': True,
        'question': question.format()
      })

    except: 
      abort(400)
  
  # Create error handlers for all expected errors including 404, 422, 400, 405 and 500.
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'resource not found'
    }), 404
  
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': 'unprocessable'
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'bad request'
    }), 400

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'method not allowed'
    }), 405

  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
      'success': False,
      'error': 500,
      'message': 'internal server error'
    }), 500

  return app