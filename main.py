from website import create_app

app = create_app()

if __name__ == '__main__':
    context = ('flask.cert', 'flask.key')
    app.run(ssl_context=context)
