import os

from brewbuddy import app

app.config.from_object('config.DevelopmentConfig')
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
