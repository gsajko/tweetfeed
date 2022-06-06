from setuptools import setup

setup(
    name="tweetfeed",
    entry_points={
        "console_scripts": [
            "tweetfeed = app.cli:app",
        ],
    },
)
