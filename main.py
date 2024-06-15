from web.base import app, database


def main():
    with app.app_context():
        database.create_all()

    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
