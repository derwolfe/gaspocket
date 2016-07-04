from setuptools import setup


if __name__ == "__main__":
    setup(
        name="gaspocket",
        version="0.1",
        description="Twitter bot to check codecov, travis, and github status",
        license="MIT",
        author="Chris Wolfe",
        author_email="chriswwolfe@gmail.com",
        packages=['gaspocket'],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        install_requires=[
            "twisted",
            "treq",
            "feedparser",
            "twython",
            "attrs"
        ],
        zip_safe=False,
    )
