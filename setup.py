from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["jaeger-client>=4.3.0",
                "opentracing>=2.3.0"]

setup(
    name="jaeger_logger_reporter",
    version="0.0.8",
    author="Cristiano Alves",
    author_email="cristiano.f.t.alves@gmail.com",
    description="Jaeger Logger Reporter",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/cristianoalves92/jaeger_logger_reporter",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
    ],
)
