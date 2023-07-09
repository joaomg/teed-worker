from setuptools import setup, find_packages

setup(
    name="teed_worker",
    version="1.0.0",
    description="Teed Worker Package",
    author="joaomg",
    author_email="joaomg@gmail.com",
    packages=find_packages(exclude=["tests"]),
    install_requires=["pika", "teed"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
