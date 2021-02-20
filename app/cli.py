from typing import Optional

import typer

app = typer.Typer()


@app.command()
def hello(name: Optional[str] = None):
    if name:
        typer.echo(f"Hello {name}")
    else:
        typer.echo("Hello World!")


@app.command()
def bye(name: Optional[str] = None):
    if name:
        typer.echo(f"Bye {name}")
    else:
        typer.echo("Goodbye!")


# TODO option for feed: onlyfollow, nofollow
# grab only people I follow, and grab people I don't follow

if __name__ == "__main__":
    app()
