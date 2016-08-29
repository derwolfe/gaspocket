from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="gaspocket",
        version="0.1",
        description="Twitter bot to check codecov, travis, and github status",
        license="MIT",
        author="Chris Wolfe",
        author_email="chriswwolfe@gmail.com",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
        ],
        zip_safe=False,
        package_dir={'': 'src'},
        packages=find_packages(where='src', exclude=[])
    )
