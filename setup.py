from pathlib import Path

if __name__ == "__main__":
    import setuptools
    setuptools.setup(
        packages=["utilitas"],
        # long_description=Path(__file__).parent / "READEME.md".read_text()
        long_description_content_type="text/markdown"
    )