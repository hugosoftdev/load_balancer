import os
#from api._01_manual_response_class import app
from api import app
# from api._03_post_method import app
# from api._04_delete_method import app
# from api._05_flask_restful_simple import app


if __name__ == '__main__':
    app.debug = True
    host = os.environ.get('IP', '0.0.0.0')
    port = int(os.environ.get('PORT', 8888))
    app.run(host=host, port=port, use_reloader=False)
