# -*- encoding: utf-8 -*-

"""
Copyright (c) 2019 - present AppSeed.us
"""

from api import app, db
from dotenv import load_dotenv
load_dotenv()
import os


@app.shell_context_processor
def make_shell_context():
    return {"app": app,
            "db": db
            }


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.environ["PORT"], ssl_insecure=True)
