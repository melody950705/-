from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run the application locally in debug mode
    app.run(debug=True)
